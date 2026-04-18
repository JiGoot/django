from django.db.models.query import QuerySet

from order.models.item import OrderItem


class OrderItemSrz:
    @staticmethod
    def default(data):
        def serialize(obj: OrderItem):
            return {
                "id": obj.pk,
                "name": obj.name,
                'price': float(obj.price),
                'discount': float(obj.discount),
                "qty": obj.qty,
                "removed": obj.removed,
            }

        if isinstance(data, OrderItem):
            return serialize(data)
        elif isinstance(data, (QuerySet, list, tuple)):
            return [serialize(obj) for obj in data if isinstance(obj, OrderItem)]
        return []

    @staticmethod
    def snapshot(data):
        def serialize(obj: OrderItem):
            return {
                "name": obj.name,
                'price': float(obj.price),
                'discount': float(obj.discount),
                "qty": obj.qty,
                "removed": obj.removed,
            }

        if isinstance(data, OrderItem):
            return serialize(data)
        elif isinstance(data, (QuerySet, list, tuple)):
            return [serialize(obj) for obj in data if isinstance(obj, OrderItem)]
        return []
