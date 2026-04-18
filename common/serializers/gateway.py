from typing import Optional, Union
from django.db.models.query import QuerySet

from common.models.gateway import Gateway


class GatewaySrz:
    @staticmethod
    def default(data: Union[Gateway, list, QuerySet]):
        def __default(obj: Gateway):
            return {
                "id": obj.id,
                "name": obj.name,
                "min": obj.min,
                "max": obj.max,
            }

        if isinstance(data, Gateway):
            return __default(data)
        elif isinstance(data, (list, QuerySet)):
            if all(isinstance(obj, Gateway) for obj in data):
                return [__default(obj) for obj in data]
