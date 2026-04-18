import logging
from rest_framework.request import Request
from branch.models.branch import Branch
from branch.models.shift import Shift
from branch.serializers.delivery_type import DeliveryTypeSrz
from branch.serializers.shift import ShiftSrz
from django.db.models.query import QuerySet
from django.core.paginator import Page
from common.serializers.vertical_type import ServiceSrz
from merchant.serializers.supplier import SupplierSrz

# Create a logger for this file
logger = logging.getLogger(__name__)
class BranchSrz:
    class Branch:
        @staticmethod
        def default(data: object):
            def __default(obj: Branch):
                serialized = {
                    "type": ServiceSrz.default(obj.type),
                    "id": obj.id,
                    "name": obj.supplier.name,
                    "label": obj.label,
                    "ept": str(obj.ept),
                    "ttr": str(obj.ttr),
                    "delay": {
                        "duration": obj.delay_duration,
                        "start": obj.delay_start.isoformat() if obj.delay_start else None,
                        "reason": obj.delay_reason,
                    },
                    "status": obj.status,
                    "currency": getattr(obj, "currency", obj.city.currency),
                    "is_active": obj.is_active,
                }
                return serialized

            if isinstance(data, Branch):
                return __default(data)
            elif isinstance(data, QuerySet) or isinstance(data, list):
                return [__default(obj) for obj in data]

    class Customer:
        @staticmethod
        def base(data: object):
            """NOTE:: For Store the [supplier] name is by convention the city name"""

            def __srz(obj: Branch):
                print("branch", obj.id, obj.type, ServiceSrz.default(obj.type))
                serialized = {
                    "id": obj.id,
                    "type": ServiceSrz.default(obj.type),
                    "supplier": SupplierSrz.Customer.default(obj.supplier),
                    "label": obj.label,
                    "ttr": str(obj.ttr),
                    "ept": str(obj.ept),
                    "delay": {
                        "duration": obj.delay_duration,
                        "start": obj.delay_start.isoformat() if obj.delay_start else None,
                        "reason": obj.delay_reason,
                    },
                    "status": obj.status,
                    "currency": obj.city.currency,
                    "location": {
                        "lat": obj.lat,
                        "lng": obj.lng,
                        "address": obj.address,
                        "landmark": obj.landmark,
                        "pickup_instructions": obj.pickup_instructions,
                    },
                }
                return serialized

            if isinstance(data, Branch):
                return __srz(data)
            elif isinstance(data, QuerySet) or isinstance(data, list):
                return [__srz(obj) for obj in data]

        @staticmethod
        def default(data: object):  # NOTE:: for Customer and Courier
            def __srz(obj: Branch):
                srz = BranchSrz.Customer.base(obj)
                srz["dial_code"] = obj.dial_code
                srz["phone"] = obj.phone
                srz["delivery_types"] = DeliveryTypeSrz.default(obj.active_delivery_types)
                srz["shifts"] = ShiftSrz.default(obj.active_shifts)
                return srz

            if isinstance(data, Branch):
                return __srz(data)
            elif isinstance(data, (list, QuerySet, Page)):
                return [__srz(obj) for obj in data]

    class Courier:
        @staticmethod
        def default(data: object):
            def __default(obj: Branch):
                serialized = {
                    "type": ServiceSrz.default(obj.type),
                    "id": obj.id,
                    "name": obj.supplier.name,
                    "label": obj.label,
                    "ttr": str(obj.ttr),
                    "ept": str(obj.ept),
                    "delay": {
                        "duration": obj.delay_duration,
                        "start": obj.delay_start.isoformat() if obj.delay_start else None,
                        "reason": obj.delay_reason,
                    },
                    "status": obj.status,
                    "currency": obj.city.currency,
                    "location": {
                        "lat": obj.lat,
                        "lng": obj.lng,
                        "address": obj.address,
                        "landmark": obj.landmark,
                        "pickup_instructions": obj.pickup_instructions,
                    },
                    "is_active": obj.is_active,
                }
                return serialized

            if isinstance(data, Branch):
                return __default(data)
            elif isinstance(data, QuerySet) or isinstance(data, list):
                return [__default(obj) for obj in data]
