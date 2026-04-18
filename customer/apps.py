import logging
import os
import sys
from django.apps import AppConfig
logger = logging.getLogger(__name__)

class CustomerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'customer'

    def ready(self) -> None:
        super().ready()

        ## <-- Skip initialization during management commands
        skip_commands = {'migrate', 'makemigrations', 'test', 'qcluster' }
        if any(cmd in sys.argv for cmd in skip_commands):
            return
        # <-- skip if under reloader
        if os.environ.get('RUN_MAIN') != 'true':
            return
        
        # Load signal handlers
        import customer.signals  

