import logging
from django.core.cache import cache
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save, post_delete
from branch.models.branch import Branch

# from common.models.catalog.category import Category
from core.utils import formattedError

# from store.models.category import StoreCategory

# logger = logging.getLogger(__name__)

# @receiver([post_save, post_delete], sender=Category, dispatch_uid=f"{__name__}.Category")
# def on_category_signal(sender, instance: Category, **kwargs):
#     logger.info(f'>>> {__name__}.{sender.__name__}. ...')

#     # Invaldate store catalog
#     try:
#         strCategories = StoreCategory.objects.filter(category=instance).select_related('store')
#         for strCat in strCategories:
#             cache.delete(strCat.store.cached.keys.store_categories)
#             cache.delete(strCat.store.cached.keys.catalog)
#     except Exception as e:
#         logger.exception(formattedError(e))


# @receiver([post_save, post_delete], sender=Branch, dispatch_uid="branch.post_change")
# def cache_invalidation_save(sender, instance, **kwargs):
#     try:

#         # NOTE:: Cache invalidation
#         cache_client = cache.client.get_client()
#         keys = cache_client.smembers(instance.cache_key_set)
#         # when using smembers in redis-py with Python 3, Each element in the set is a bytes object.
#         for bkey in keys:
#             cache.delete(bkey.decode("utf-8"))
#     except Exception as e:
#         logger.exception(formattedError(e))


import logging
from django.core.cache import cache
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save, post_delete
from core.utils import formattedError

# from store.models.category import StoreCategory

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Branch, dispatch_uid=f"{__name__}")
def cache_invalidation(sender, instance: Branch, **kwargs):
    logger.info(f">>> {__name__}.{sender.__name__} ...")
    # INFO:: Invalidate branch related cache
    try:
        cache.delete(instance.cached.keys.active_orders())


    except Exception as e:
        logger.exception(formattedError(e))
