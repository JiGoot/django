import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver
from django.core.cache import cache
from common.models import Zone
from core.utils import formattedError

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Zone)
def clear_neighbors(sender, instance: Zone, **kwargs):
    # Remove neighbouring zones cache
    try:
        key = instance.cached.keys.neighbors
        print(f"Invalidate :{key} ")
        cache.delete(key)
    except Exception as e:
        logger.error(formattedError(e))
