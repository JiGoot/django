import logging
import sys
from django.apps import AppConfig
logger = logging.getLogger(__name__)

class CourierConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courier'

    def ready(self) -> None:
        import courier.models  # Ensure models are loaded

        # Skip initialization during management commands
        skip_commands = {'migrate', 'makemigrations', 'test'}
        if any(cmd in sys.argv for cmd in skip_commands):
            return

        # Load signal handlers
        import courier.signals

        super().ready()
