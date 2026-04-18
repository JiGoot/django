import os
import sys

# from core.decorators.register_signals import register_signals
from django.apps import AppConfig
from core.utils import Logger, formattedError


logger = Logger(__name__)

class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"

    def ready(self):
        # Initialize RabbitMQ publisher
        # <-- Skip initialization during management commands
        if os.environ.get("RUN_MAIN") == "true":
            try:
                from core.rabbitmq.broker import publisher

                publisher.connect()
            except Exception as e:
                logger.error(
                    f"\033[91mError initializing RabbitMQ publisher: \n{formattedError(e)}\033[0m"
                )
                sys.exit(1)  # clean, intentional failure to allow systemd to restart
