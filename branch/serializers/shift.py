from typing import Union
from django.db.models.query import QuerySet

from branch.models.shift import Shift


class ShiftSrz:
    @staticmethod
    def default(data: object):
        def __default(obj: Shift):
            return {
                "id": obj.pk,
                "weekdays": obj.weekdays,
                "start": obj.start,
                "end": obj.end,
            }

        if isinstance(data, Shift):
            return __default(data)
        elif isinstance(data, QuerySet) or isinstance(data, list):
            return [__default(obj) for obj in data]
