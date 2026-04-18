from typing import Optional, Union
from django.db.models.query import QuerySet
from common.models.boundary.zone import Zone


class ZoneSrz:

    @staticmethod
    def __map(obj: Zone):
        return {
            "id": obj.pk,  # NOTE we use suppplier.pk instead of kitchen.pk, for the favorit feature
            "name": obj.name,
            "city": obj.city.name,
            "detour_index": obj.detour_index,
            "start": obj.start,
            "end": obj.end,
            # for polygon hole use [1] if any
            "coords": obj.coords,
        }

    @staticmethod
    def map(data: object):
        if isinstance(data, Zone):
            return ZoneSrz.__map(data)
        elif isinstance(data, (list, QuerySet)):
            return [ZoneSrz.__map(obj) for obj in data]

    @staticmethod
    def __default(obj: Zone):
        return {
            "id": obj.pk,  # NOTE we use suppplier.pk instead of kitchen.pk, for the favorit feature
            "name": obj.name,
            "detour_index": float(obj.detour_index),
            "start": obj.start.isoformat(),
            "end": obj.end.isoformat(),
            "lat": obj.lat,
            "lng": obj.lng,
        }

    @staticmethod
    def default(data: object):
        if isinstance(data, Zone):
            return ZoneSrz.__default(data)

        elif isinstance(data, (list, QuerySet)):
            if all(isinstance(obj, Zone) for obj in data):
                return [ZoneSrz.__default(obj) for obj in data]
