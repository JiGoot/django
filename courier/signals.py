from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver
from django.core.cache import cache
from core.utils import delete_image_utility
from courier.models import Courier, CourierShift

@receiver(post_delete, sender=Courier)
def post_delete_courier(sender, instance, **kwargs):
    delete_image_utility(instance)


@receiver([post_save, post_delete], sender=CourierShift)
def post_update_shifts(sender, instance: CourierShift, **kwargs):
    cache.delete(instance.courier.cached.keys.shifts)
    # TODO:: Delete City courier's cached slots corresponding 
    # to the courier'shift date
    cached= instance.courier.city.cached
    cache.delete(cached.getKey(cached.prefix.courier_slots, instance.date))

