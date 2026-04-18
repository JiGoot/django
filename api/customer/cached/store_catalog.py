import logging
from typing import Optional

import pytz
from affiche.models import Affiche
from common.models.boundary.city import City
from django.db.models.query import QuerySet
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count, Q
from common.models.boundary.zone import Zone


class CachedStoreCatalog:
    logger = logging.getLogger(__name__)

    class Keys:
        def __init__(self, city: City, zone: Zone, cell_id: Optional[int]):
            self.affiches = f"city-{city.id}:affiches"
            self.branches = f"city-{city.id}:stores"  # city-specific
            self.store = f"h3-{cell_id}:branch" if cell_id else None
            self.kitchens = f"h3-{cell_id}:branch" if cell_id else None

    def __init__(self, city: City, zone: Zone, cell_id: Optional[int]) -> None:
        self.city = city
        self.zone = zone
        self.cell_id = cell_id
        self.keys = self.Keys(city, zone, cell_id)

    @property
    def affiches(self) -> QuerySet:
        try:
            cached = cache.get(self.keys.affiches)
            if cached:
                return cached
        except Exception:
            cache.delete(self.keys.affiches)

        tz = pytz.timezone(self.city.timezone)
        local_now = timezone.now().astimezone(tz)

        qs = Affiche.objects.filter(
            Q(is_active=True),
            Q(
                Q(start__lte=local_now, end__gte=local_now)
                | Q(start__isnull=True, end__isnull=True)
            ),
        )[:4]

        cache.set(self.keys.affiches, qs, timeout=900)
        return qs
