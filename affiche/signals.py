from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch.dispatcher import receiver
from django.core.cache import cache
from affiche.models import Affiche
from common.models.boundary.city import City


# Signal receiver to clear cache when Affiche is saved, updated or deleted
@receiver([post_save, post_delete], sender=Affiche, dispatch_uid="post_update_affiche")
def post_update_affiche(sender, instance: Affiche, **kwargs):
    city: City = instance.city
    cache.delete(city.cached.keys.affiches)