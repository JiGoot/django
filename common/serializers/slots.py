from typing import Optional, Union
from django.db.models.query import QuerySet
from common.models.slot import Slot


class SlotSrz:
    """
    Serialize [Order] for [Jigoot kitchen] app's [homePage].
    NOTE For [Jigoot kitchen] the user is defacto a kitchen, so kitchen's details do
    not need to be sent back to the kitchen.
    """

    @staticmethod
    def default(data: object):
        def __srz(obj: Slot):
            return {
                "id": obj.pk,
                "start": obj.start,
                "end": obj.end,
                "max_capacity": obj.max_capacity,
                # Added from annotation count of registed shifts for a given day
                "max_capacity": obj.max_capacity,  # total allowed
                "capacity": getattr(obj, "capacity", 0),  # number of shifts taken
            }

        if isinstance(data, Slot):
            return __srz(data)
        elif isinstance(data, (list, QuerySet)):
            return [__srz(order) for order in data]
