from datetime import datetime
import importlib
from multiprocessing import Process
import time
from django.core.management.base import BaseCommand
from core.rabbitmq.broker import RabbitMQ
from typing import Any, Callable


class Command(BaseCommand):
    help = "RabbitMQ consumer worker"

    def add_arguments(self, parser):

        parser.add_argument(
            "--workers",
            type=int,
            default=2,
            help="Number of worker processes",
        )

    def handle(self, *args, **options):
        workers = options["workers"]
        processes = []

        for _ in range(workers):
            p = Process(target=Command.run_worker, daemon=True)
            p.start()
            processes.append(p)
            time.sleep(1)  # Staggered start for workers

        # Keep main process alive
        try:
            for p in processes:
                p.join()
        except KeyboardInterrupt:
            for p in processes:
                p.terminate()

    @staticmethod
    def run_worker():
        broker = RabbitMQ(is_publisher=False)
        import os, django

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jigoot.settings")
        django.setup()

        broker.consume()
