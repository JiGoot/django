from rest_framework.request import Request
from django.db.models.query import QuerySet

from typing import Optional, Union

from branch.models.tag import Tag
from common.serializers.vertical_type import ServiceSrz


class TagSrz:
    @staticmethod
    def default(data: object) -> Union[dict, list]:
        def __default(obj: Tag):
            return {
                "id": obj.pk,
                "index": obj.index,
                "name": obj.name,
                "type": ServiceSrz.default(obj.type),
                "image": obj.image.url if obj.image else None,
            }

        if isinstance(data, Tag):
            return __default(data)
        elif isinstance(data, QuerySet) or isinstance(data, list):
            return [__default(obj) for obj in data]
