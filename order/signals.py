import json
from core import mqtt
from order.models.order import Order
from order.serializers.order import OrderSrz
from core.rabbitmq.broker import publisher
from core.utils import formattedError
from django.core.cache import cache
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save, post_delete
import logging
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Order)
def on_order_post(sender, instance: Order, **kwargs):
    try:
        # MQTT broadcast
        payload = {
            "id": instance.id,
            "code": instance.code,
            "status": instance.status,
        }
        # Publish to branch topic
        mqtt.publish_message(f"orders/branch/{instance.branch.id}/", payload)
        # Publish to customer topic
        mqtt.publish_message(f"orders/customer/{instance.customer.id}/", payload)
        # Publish to courier topic
        if instance.courier and instance.status in [
            Order.Status.accepted,
            Order.Status.ready,
            Order.Status.picked_up,
        ]:
            mqtt.publish_message(
                f"orders/courier/{instance.courier.id}/",
                OrderSrz.Courier.default(instance),
            )

        # Cache invalidation
        cache.delete(instance.branch.cached.keys.active_orders())
        if instance.courier: 
            cache.delete(instance.courier.cached.keys.active_orders())

        # Map status to corresponding cache key
        # status_key_map = {
        #     Order.Status.placed: instance.branch.cached.keys.placed_orders,
        #     Order.Status.accepted: instance.branch.cached.keys.accepted_orders,
        #     Order.Status.ready: instance.branch.cached.keys.ready_orders,
        # }

        # # Clear relevant cache if status matches
        # cache_key = status_key_map.get(instance.status)
        # if cache_key:
        #     cache.delete(cache_key)
    except Exception as e:
        logger.error(formattedError(e))


"""
=========================================================================
"""


# @receiver(pre_save, sender=Order)
# def snapshot_order_before_update(sender, instance: Order, **kwargs):
#     if not instance.pk:
#         return  # only create snapshot for updates
#     # TODO:: Use qcluster publisher
#     StoreOrderSnapshot.objects.create(src=instance, values=OrderSrz.snapshot(instance))


"""
=========================================================================
"""


# @receiver(pre_save, sender=OrderItem)
# def order_item_snapshot(sender, instance: OrderItem, **kwargs):
#     # Define which fields you want to track
#     if not instance.pk:
#         return  # Skip for new instances
#     # TODO:: Use qcluster publisher
#     StoreOrderItemSnapshot.objects.create(src=instance, values=OrderItemSrz.snapshot(instance))


"""
=========================================================================
"""
