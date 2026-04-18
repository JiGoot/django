from typing import TYPE_CHECKING
from datetime import timedelta
import logging
from django.core.cache import cache
from django.db.models.query import QuerySet

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from common.models.boundary.zone import Zone


class CachedZone:
    logger = logging.getLogger(__name__)

    class Key:
        def __init__(self, instance: 'Zone'):
            base = f'zone-{instance.id}'
            self.neighbors = f'{base}:neighbors'
            

    def __init__(self, zone: 'Zone') -> None:
        self.instance = zone
        self.keys = self.Key(zone)

    @property
    def neighbors(self) -> QuerySet:
        '''Retrieve neighbors for the zone or query and cache them'''
        try:
            cached = cache.get(self.keys.neighbors)
            if isinstance(cached, QuerySet):
                return cached
        except:
            cache.delete(self.keys.neighbors)
        qs = self.instance.neighbors.filter(is_active=True)
        cache.set(self.keys.neighbors, qs, timeout=timedelta(hours=1).total_seconds())
        return qs
    
