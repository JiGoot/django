from django.db.models.query import QuerySet

from typing import Optional, Union
from common.models.catalog.category import Category


class CategorySrz:
    @staticmethod
    def default(data: object) -> Union[dict, list]:
        def __default(obj: Category):
            return {
                "id": obj.pk,
                "name": obj.name,
                "image": obj.image.url if obj.image else None,
            }

        if isinstance(data, Category):
            return __default(data)
        elif isinstance(data, QuerySet) or isinstance(data, list):
            return [__default(obj) for obj in data]
