from branch.serializers.tag import TagSrz
from merchant.models.supplier import Supplier
from django.db.models import QuerySet


class SupplierSrz:

    class Customer:
        @staticmethod
        def default(data: object):  # NOTE:: for Customer and Courier
            def __srz(obj: Supplier):
                serialized = {
                    "id": obj.id,
                    "name": obj.name,
                    "tags": TagSrz.default(obj.tags),
                    "logo": obj.logo.url if obj.logo else None,
                    "image": obj.image.url if obj.image else None,
                    "description": obj.description,
                }
                return serialized

            if isinstance(data, Supplier):
                return __srz(data)
            elif isinstance(data, QuerySet) or isinstance(data, list):
                return [__srz(obj) for obj in data]

            if isinstance(data, Supplier):
                return __srz(data)
            elif isinstance(data, (list, QuerySet)):
                return [__srz(obj) for obj in data]
