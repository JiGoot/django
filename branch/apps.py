import logging
from django.apps import AppConfig

from core.utils import formattedError

logger = logging.getLogger(__name__)

class BranchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'branch'

    # @register_signals() 
    def ready(self):
        # Import signals to register them
        try:
            import branch.signals
            logger.info("Branch signals loaded")
        except ImportError as e:
            logger.exception(f"Failed to load branch signals: {formattedError(e)}")
        ...
        # Any app-specific logic (optional)
        pass
