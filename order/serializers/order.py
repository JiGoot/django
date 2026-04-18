from rest_framework.request import Request
from django.db.models.query import QuerySet
from branch.serializers.branch import BranchSrz
from customer.serializers import CustomerSrz
from common.serializers.zone import ZoneSrz
from courier.serializers import CourierSrz
from order.models.order import Order
from order.serializers.item import OrderItemSrz
from django.core.paginator import Page


class OrderSrz:
    @staticmethod
    def snapshot(data):
        def serialize(obj: Order):
            return {
                "status": obj.status,
                "subtotal": float(obj.subtotal),
                "ept": obj.ept,
            }

        if isinstance(data, Order):
            return serialize(data)
        elif isinstance(data, (QuerySet, list, tuple)):
            return [serialize(obj) for obj in data if isinstance(obj, Order)]
        return []

    class Branch:

        @staticmethod
        def listTile(data: object):
            def __srz(obj: Order):
                _payment_status, _amount = obj.payment_status
                updated_at = getattr(obj, "updated_at", None)
                return {
                    # NOTE we use suppplier.pk instead of kitchen.pk, for the favorit feature
                    "id": obj.pk,
                    "status": obj.status,
                    "ept": obj.ept,
                    "code": obj.code,
                    # Payment
                    "payment": {
                        "status": _payment_status,
                        "amount": float(_amount),
                    },
                    "subtotal": float(obj.subtotal),
                    "currency": obj.currency,
                    # Dates
                    "placed_at": obj.placed_at.isoformat(),
                    "updated_at": updated_at.isoformat() if updated_at else None,
                }

            if isinstance(data, Order):
                return __srz(data)

            if isinstance(data, (list, QuerySet, Page)):
                return [__srz(obj) for obj in data if isinstance(obj, Order)]

            return None  # or raise TypeError("Invalid data type for listTile")

        @staticmethod
        def default(data: object):
            def __srz(obj: Order):
                _payment_status, _amount = obj.payment_status
                updated_at = getattr(obj, "updated_at", None)
                # _cancelled: CancelledOrder = CancelledOrder.objects.get_or_none()
                return {
                    "id": obj.pk,
                    "customer": CustomerSrz.Branch.default(obj.customer),
                    "courier": (CourierSrz.Branch.default(obj.courier) if obj.courier else None),
                    "status": obj.status,
                    "urgency_score": getattr(obj, "urgency_score", None),
                    "time_in_status": getattr(obj, "time_in_status", None),
                    "ept": str(obj.ept),
                    "code": obj.code,
                    "subtotal": float(obj.subtotal),
                    "currency": obj.currency,
                    "payment": {
                        "status": _payment_status,
                        "amount": float(_amount),
                    },
                    # REMOVE:
                    # "address": obj.address,
                    # "landmark": obj.landmark,
                    # "pickup_instructions": obj.pickup_instructions,
                    "placed_at": obj.placed_at.isoformat(),
                    "updated_at": updated_at.isoformat() if updated_at else None,
                }

            if isinstance(data, Order):
                return __srz(data)
            if isinstance(data, (list, QuerySet, Page)):
                return [__srz(obj) for obj in data if isinstance(obj, Order)]

    """
    ----------------------------------------------------------------------------
    ----------------------------------------------------------------------------
    ----------------------------------------------------------------------------
    """

    class Courier:

        @staticmethod
        def listTile(data: object):
            def __srz(obj: Order):
                _payment_status, _amount = obj.payment_status
                updated_at = getattr(obj, "updated_at", None)
                return {
                    # NOTE we use suppplier.pk instead of kitchen.pk, for the favorit feature
                    "id": obj.pk,
                    "customer": CustomerSrz.Courier.default(obj.customer),
                    "branch": BranchSrz.Courier.default(obj.branch),
                    "ept": obj.ept,
                    "code": obj.code,
                    "pin": obj.pin,
                    "status": obj.status,
                    # Locations
                    "pickup": {
                        "lat": obj.branch.lat,
                        "lng": obj.branch.lng,
                        "address": obj.branch.address,
                        "landmark": obj.branch.landmark,
                    },
                    "dropoff": {
                        "lat": obj.dropoff_lat,
                        "lng": obj.dropoff_lng,
                        "address": obj.dropoff_address,
                        "landmark": obj.dropoff_landmark,
                        "pickup_instructions": obj.dropoff_courier_instructions,
                    },
                    # scheduling
                    "scheduled": {
                        "dropoff": {
                            "data": obj.dropoff_date,
                            "start": obj.dropoff_slot_start,
                            "end": obj.dropoff_slot_end,
                        }
                    },
                    # Payment
                    # NOTE: Courier do not need to knpw the subtotal , but only what they need to collect
                    "payment": {
                        "status": _payment_status,
                        "amount": float(_amount),
                        "currency": obj.currency,
                    },
                    # Dates
                    "placed_at": obj.placed_at.isoformat(),
                    "updated_at": updated_at.isoformat() if updated_at else None,
                }

            if isinstance(data, Order):
                return __srz(data)

            if isinstance(data, (list, QuerySet, Page)):
                return [__srz(obj) for obj in data if isinstance(obj, Order)]

            return None  # or raise TypeError("Invalid data type for listTile")

        @staticmethod
        def default(data: object):
            def __srz(obj: Order):
                _payment_status, _amount = obj.payment_status
                updated_at = getattr(obj, "updated_at", None)
                # _cancelled: CancelledOrder = CancelledOrder.objects.get_or_none()
                return {
                    "id": obj.pk,
                    "customer": CustomerSrz.Branch.default(obj.customer),
                    "branch": BranchSrz.Branch.default(obj.branch),
                    "ept": str(obj.ept),
                    "code": obj.code,
                    "status": obj.status,
                    "subtotal": float(obj.subtotal),
                    "small_order_fee": float(obj.small_order_fee),
                    "delivery_fee": float(obj.delivery_fee),
                    "currency": obj.currency,
                    "payment": {
                        "status": _payment_status,
                        "amount": float(_amount),
                    },
                    "dropoff": {
                        "lat": obj.dropoff_lat,
                        "lng": obj.dropoff_lng,
                        "address": obj.dropoff_address,
                        "landmark": obj.dropoff_landmark,
                        "pickup_instructions": obj.dropoff_courier_instructions,
                    },
                    # Dates
                    "placed_at": obj.placed_at.isoformat(),
                    "updated_at": updated_at.isoformat() if updated_at else None,
                }

            if isinstance(data, Order):
                return __srz(data)
            if isinstance(data, (list, QuerySet, Page)):
                return [__srz(obj) for obj in data if isinstance(obj, Order)]

        # @staticmethod
        # def listTile(data: object):
        #     def __srz(obj: Order):
        #         _payment_status, _amount = obj.payment_status
        #         return {
        #             # NOTE we use suppplier.pk instead of kitchen.pk, for the favorit feature
        #             "id": obj.pk,
        #             "type": obj.type,
        #             "status": obj.status,
        #             "ept": obj.ept,
        #             "code": obj.code,
        #             "delivery_fee": obj.delivery_fee,
        #             "currency": obj.currency,
        #             "payment": {
        #                 "status": _payment_status,
        #                 "amount": _amount,
        #             },
        #             "lat": obj.lat,
        #             "lng": obj.lng,
        #             "accepted_at": (
        #                 obj.accepted_at.isoformat() if obj.accepted_at else None
        #             ),
        #             "delivered_at": (
        #                 obj.delivered_at.isoformat() if obj.delivered_at else None
        #             ),
        #         }

        #     if isinstance(data, Order):
        #         return __srz(data)

        #     if isinstance(data, (list, QuerySet, Page)):
        #         return [__srz(obj) for obj in data if isinstance(obj, Order)]

        # def default(data: object):
        #     def __srz(obj: Order):
        #         _payment_status, _amount = obj.payment_status
        #         return {
        #             # NOTE we use suppplier.pk instead of kitchen.pk, for the favorit feature
        #             "id": obj.pk,
        #             "customer": CustomerSrz.Courier.default(obj.customer),
        #             "type": obj.type,
        #             # "branch": BranchSrz.Courier.default(obj.branch),
        #             "status": obj.status,
        #             "urgency_score": getattr(obj, "urgency_score", None),
        #             "time_in_status": getattr(obj, "time_in_status", None),
        #             "ept": obj.ept,
        #             "total": obj.total,
        #             "delivery_fee": obj.delivery_fee,
        #             "currency": obj.currency,
        #             "payment": {
        #                 "status": _payment_status,
        #                 "amount": _amount,
        #             },
        #             "code": obj.code,
        #             "lat": obj.lat,
        #             "lng": obj.lng,
        #             "zone": ZoneSrz.default(obj.zone) if obj.zone else None,
        #             "address": (
        #                 obj.address if obj.status == Order.Status.picked_up else None
        #             ),
        #             "landmark": (
        #                 obj.landmark if obj.status == Order.Status.picked_up else None
        #             ),
        #             "placed_at": obj.placed_at.isoformat(),
        #             "updated_at": getattr(obj, "updated_at", None),
        #         }

        #     if isinstance(data, Order):
        #         return __srz(data)

        #     if isinstance(data, (list, QuerySet, Page)):
        #         return [__srz(obj) for obj in data if isinstance(obj, Order)]

    """
    ----------------------------------------------------------------------------
    ----------------------------------------------------------------------------
    ----------------------------------------------------------------------------
    """

    class Customer:
        @staticmethod
        def basic(data: object):
            """Only required fields by the customer"""

            def __srz(obj: Order):
                _payment_status, _amount = obj.payment_status
                updated_at = getattr(obj, "updated_at", None)
                serialized = {
                    "id": obj.pk,
                    "branch": BranchSrz.Customer.base(obj.branch),
                    "code": obj.code,
                    "pin": obj.pin,
                    "status": obj.status,
                    # Drop-off location
                    "dropoff": {
                        "lat": obj.dropoff_lat,
                        "lng": obj.dropoff_lng,
                        "address": obj.dropoff_address,
                        "landmark": obj.dropoff_landmark,
                        "pickup_instructions": obj.dropoff_courier_instructions,
                        "scheduled": {
                            "data": obj.dropoff_date,
                            "start": obj.dropoff_slot_start,
                            "end": obj.dropoff_slot_end,
                        },
                    },
                    # scheduling
                    "scheduled": {
                        "data": obj.dropoff_date,
                        "start": obj.dropoff_slot_start,
                        "end": obj.dropoff_slot_end,
                    },
                    # Payment
                    "payment": {
                        "status": _payment_status,
                        "amount": float(_amount),
                    },
                    "subtotal": float(obj.subtotal),
                    "small_order_fee": float(obj.small_order_fee),
                    "service_fee": float(obj.service_fee),
                    "delivery_fee": float(obj.delivery_fee),
                    "currency": obj.currency,
                    # Dates
                    "placed_at": obj.placed_at.isoformat(),
                    "updated_at": updated_at.isoformat() if updated_at else None,
                }
                return serialized

            if isinstance(data, Order):
                return __srz(data)

            if isinstance(data, (list, QuerySet, Page)):
                return [__srz(obj) for obj in data if isinstance(obj, Order)]

        def default(data: object):
            def __srz(obj: Order):
                srz = OrderSrz.Customer.basic(obj)
                srz["courier"] = CourierSrz.Customer.default(obj.courier)
                return srz

            if isinstance(data, Order):
                return __srz(data)

            if isinstance(data, (list, QuerySet, Page)):
                return [__srz(obj) for obj in data if isinstance(obj, Order)]
