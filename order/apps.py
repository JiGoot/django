import logging
import os
import sys
from django.apps import AppConfig

from core.utils import formattedError

logger = logging.getLogger(__name__)
class OrderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'order'

    def ready(self) -> None:
        # super().ready()
        ## <-- Skip initialization during management commands
        skip_commands = {'migrate', 'makemigrations', 'test', 'qcluster' }
        if any(cmd in sys.argv for cmd in skip_commands):
            return
        # # <-- skip if under reloader
        # if os.environ.get('RUN_MAIN') != 'true':
        #     return
        
        # Load signal handlers
        try:
            import order.signals
            logger.info("Order signals loaded")
        except ImportError as e:
            logger.exception(f"Failed to load order signals: {formattedError(e)}")
