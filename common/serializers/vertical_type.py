from django.db.models.query import QuerySet
from typing import Optional, Union
from common.models.city_service import CityService
from common.models.service import Service




class ServiceSrz:
    @staticmethod
    def default(data: object, request=None):
        def __default(obj: Service) -> Optional[dict]:
            return {
                "id": obj.pk,
                "name": obj.name,
                "logo": obj.logo.url if obj.logo else None,
                "image": obj.image.url if obj.image else None,
                "age_check": obj.age_check,
                "is_active": obj.is_active,
            }

        if isinstance(data, Service):
            return __default(data)
        elif isinstance(data, (list, QuerySet)):
            if all(isinstance(obj, (Service)) for obj in data):
                return [__default(obj) for obj in data]
            
class CityServiceSrz:
    class Customer:
        @staticmethod
        def default(data: object, request=None):
            def __default(obj: CityService) -> Optional[dict]:
                return {
                    "id": obj.pk,
                    "name": obj.service.name,
                    "logo": obj.service.logo.url if obj.service.logo else None,
                    "image": obj.service.image.url if obj.service.image else None,
                    "is_branch_less": obj.service.is_branch_less,
                    "age_check": obj.service.age_check,
                    "min_age": obj.min_age,
                    "is_active": obj.is_active,
                }

            if isinstance(data, CityService):
                return __default(data)
            elif isinstance(data, (list, QuerySet)):
                if all(isinstance(obj, (CityService)) for obj in data):
                    return [__default(obj) for obj in data]
