from contextlib import contextmanager
from datetime import datetime
import json
import os
import time
from dotenv import load_dotenv
import pika
from core import settings
from core.rabbitmq.utils import process_task
from core.utils import Logger, formattedError
from pika.exceptions import (
    AMQPConnectionError,
    AMQPChannelError,
    StreamLostError,
    ConnectionClosedByBroker,
)

load_dotenv(override=True)

logger = Logger(__name__)
AMQP_ERRORS = (
    StreamLostError,
    ConnectionClosedByBroker,
    AMQPConnectionError,
    AMQPChannelError,
)


class RabbitMQ:
    def __init__(self, is_publisher: bool = False):
        self.host = os.getenv("AMQP_URL")

        self.is_publisher = is_publisher
        self.pid = os.getpid()
        self.tag = f"publisher-{self.pid}" if self.is_publisher else f"consumer-{self.pid}"
        self.app = "Django Publisher" if self.is_publisher else "Django Worker"
        self.backend = settings.Q_CLUSTER.get("backend", {})
        self.queue = settings.Q_CLUSTER.get("queue", "tasks")
        # Total number of retries is `self.retry`*`max_attempts`
        self.retry = settings.Q_CLUSTER.get("retry", 5)
        self.max_attempts = settings.Q_CLUSTER.get("max_attempts", 5)
        self.params = pika.URLParameters(self.host)
        self.params.client_properties = {
            "connection_name": self.tag,
            "app": self.app,
            "platform": "JiGoot",
            "version": settings.VERSION,
        }

        # Don't initialize connection here
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish RabbitMQ connection (called within worker process)"""
        if self.connection and self.connection.is_open and self.channel and self.channel.is_open:
            return

        self.connection = pika.BlockingConnection(self.params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue, durable=True)
        if not self.is_publisher:
            self.channel.basic_qos(prefetch_count=1)  # one message at a time per worker
        logger.success(f"✅ < {self.tag} > connected")

    def close(self):
        """Clean up RabbitMQ connection and channel"""
        try:
            if getattr(self, "channel", None) and self.channel.is_open:
                self.channel.close()
            if getattr(self, "connection", None) and self.connection.is_open:
                self.connection.close()
        except Exception as e:
            logger.warning(f"Error on closing RabbitMQ connection: {formattedError(e)}")

    @contextmanager
    def retries(self):
        attempts = 0
        while True:
            try:
                # NOTE:: Code is executed within this block,
                # right before yielding
                yield
                # successful execution, exit the loop
                # whereas `return` would exit the context resulting in no further retries
                break
            except KeyboardInterrupt:
                logger.info(f"\033[96mWorker (PID: {self.pid}) closed\033[0m")
                break  # clean exit
            except AMQP_ERRORS as e:
                attempts += 1
                if attempts > self.max_attempts:
                    logger.error(f"🛑 {self.tag} failed permanently: {formattedError(e)}")
                    raise
                logger.warning(
                    f"⚠️ {self.tag} failed. Retrying in {self.retry}s ({attempts}/{self.max_attempts})"
                )
                time.sleep(self.retry)

    DEFAULT_TTL = 72 * 60 * 60  # 3 days in seconds

    def publish(self, func, *args, ttl=None, attempts=None, created_at=None, **kwargs):
        """ttl: Time to live for the message in seconds"""
        if callable(func):
            func = f"{func.__module__}.{func.__qualname__}"

        ttl_sec = ttl if ttl else self.DEFAULT_TTL

        payload = {"func": func, "args": args or [], "kwargs": kwargs or {}}

        # Used to expire message at consumer level
        payload["created_at"] = created_at if created_at else time.time()
        payload["max_age"] = ttl_sec
        payload["attempts"] = attempts if attempts is not None else 0

        with self.retries():
            self.connect()  # Ensure connection is ready
            self.channel.basic_publish(
                exchange="",
                routing_key=self.queue,
                body=json.dumps(payload),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    expiration=str(int(ttl_sec * 1000)),  # RabbitMQ expects ms
                ),
            )

    def consume(self):
        def on_message(ch, method, properties, body):
            def safe_ack():
                if ch.is_open:
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            def safe_nack(requeue=False):
                if ch.is_open:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=requeue)

            data = {}
            try:
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    logger.error(f"Invalid message: {body}")
                    return safe_nack()

                func = data.get("func")
                args = data.get("args", [])
                kwargs = data.get("kwargs", {})
                process_task(func, *args, **kwargs)
                safe_ack()
            except Exception as e:
                now = time.time()
                created_at = data.get("created_at", now)
                max_age = data.get("max_age", 0)

                # --- Check if message expired ---
                remaining = max_age - (now - created_at)
                if remaining < 5 or (max_age and now - created_at > max_age):  # less than 5 seconds left
                    return safe_nack()

                attempts = data.get("attempts", 0)
                if attempts < 5:
                    attempts += 1
                    remaining = max(0, max_age - (now - created_at))

                    try:
                        self.publish(
                            func,
                            *args,
                            attempts=attempts,
                            ttl=remaining,
                            created_at=created_at,
                            **kwargs,
                        )
                        safe_ack()  # acknowledge old
                    except Exception:
                        safe_nack(requeue=True)

                    logger.warning(f"Retry attempt: {attempts} for task {func}")
                    # Too many retries → discard / dead-letter
                else:
                    logger.error(f"🛑 {formattedError(e)}")
                    safe_nack()

        with self.retries():
            self.connect()
            self.channel.basic_consume(
                queue=self.queue,
                on_message_callback=on_message,
            )
            # Log worker start
            now = datetime.now().isoformat(sep=" ", timespec="seconds")
            logger.warning(f"\033[96m[{now}] > {self.tag} listening...\033[0m")
            self.channel.start_consuming()


# Singleton instance
publisher = RabbitMQ(is_publisher=True)
