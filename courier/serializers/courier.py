from django.db.models.query import QuerySet
from courier.models import Courier
from typing import Optional, Union


class CourierSrz:
    """
    Serialize [Order] for [Jigoot kitchen] app's [homePage].
    NOTE For [Jigoot kitchen] the user is defacto a kitchen, so kitchen's details do
    not need to be sent back to the kitchen.
    """

    class Branch:

        @staticmethod
        def default(data: object) -> Optional[Union[dict, list]]:
            def __srz(obj: Courier):
                return {
                    "id": obj.pk,
                    "name": obj.user.name,
                    "last_name": obj.user.last_name,
                    "dial_code": obj.user.dial_code,
                    "phone": obj.user.phone,
                    "image": obj.user.image.url if obj.user.image else None,
                }

            if isinstance(data, Courier):
                return __srz(data)
            elif isinstance(data, QuerySet):
                if data.model == Courier:
                    return [__srz(order) for order in data]
            return None

    class Courier:

        @staticmethod
        def default(data: object) -> Optional[Union[dict, list]]:
            def __srz(obj: Courier):
                return {
                    "id": obj.pk,
                    "name": obj.user.name,
                    "last_name": obj.user.last_name,
                    # "dial_code": obj.user.dial_code,
                    # "phone": obj.user.phone,
                    # "email": obj.user.email,
                    "image": obj.user.image.url if obj.user.image else None,
                    "status": obj.status,
                    "paused_at": obj.paused_at,
                    "can_dash_now": obj.can_dash_now,
                    "max_slots_per_day": obj.max_slots_per_day,
                    "max_slots_per_week": obj.max_slots_per_week,
                }

            if isinstance(data, Courier):
                return __srz(data)
            elif isinstance(data, QuerySet):
                if data.model == Courier:
                    return [__srz(order) for order in data]
            return None

    class Customer:
        @staticmethod
        def default(data: object):
            return CourierSrz.Branch.default(data)
