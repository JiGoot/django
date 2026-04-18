from django.core.cache import cache
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save, post_delete
import logging
from django.db.models.signals import pre_save, pre_delete
from core.utils import  formattedError

from order.models.order import Order
from customer.models.payment import Payment
logger = logging.getLogger(__name__)

# TODO:: Refactor
# TODO:: Use qcluster publisher
@receiver([post_save,], sender=Payment)
def on_payment_post(sender, instance: Payment, **kwargs):
    try:
        order:Order = instance.order
        # Map status to corresponding cache key
        status_key_map = {
            Order.Status.placed: order.branch.cached.keys.placed_orders,
            Order.Status.accepted:  order.branch.cached.keys.accepted_orders,
            Order.Status.ready:  order.branch.cached.keys.ready_orders,
        }

        # Clear relevant cache if status matches
        cache_key = status_key_map.get(order.status)
        if cache_key:
            cache.delete(cache_key)
    except Exception as e:
        logger.error(formattedError(e))
