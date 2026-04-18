# import logging
# from django.db.models.signals import post_save, post_delete
# from django.dispatch.dispatcher import receiver
# from django.core.cache import cache
# from branch.models.tag import Tag
# from common.models.boundary.city import City
# from core.utils import formattedError


# logger = logging.getLogger(__name__)

# @receiver([post_save, post_delete], sender=Tag)
# def post_update_tag(sender, instance: Tag, **kwargs):
#     # Remove cities tags cache 
#     try:
#         for city in instance.cities.only('id'):
#             if isinstance(city, City):
#                 cache.delete(city.cached.keys.tags) 
#     except Exception as e:
#         logger.error(formattedError(e))