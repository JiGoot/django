from branch.models.branch import Branch
from branch.models.delivery_type import DeliveryType
from django.db.models.query import QuerySet


class DeliveryTypeSrz:
    @staticmethod
    def default(data: object):
        def __default(obj: DeliveryType):
            serialized = {
                "id": obj.id,
                "code": obj.code,
                "base_dispatch_buffer": obj.base_dispatch_buffer,
                "max_dispatch_buffer": obj.max_dispatch_buffer,
                "extra_fee": obj.extra_fee,
                "cutoff_time": obj.cutoff_time if obj.cutoff_time else None,
            }
            return serialized

        if isinstance(data, Branch):
            return __default(data)
        elif isinstance(data, QuerySet) or isinstance(data, list):
            return [__default(obj) for obj in data]
