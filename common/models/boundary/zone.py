from django.utils.translation import gettext_lazy as _
import logging
from django.db import models
from common.cached.zone import CachedZone
from core.managers import ObjectsManager

logger = logging.getLogger(__name__)


class Zone(models.Model):
    '''
    [lat], [lng] represent the zone center location used  
     - for courier's navigation or 
     - as a gathering point for couriers
    '''
    city = models.ForeignKey('common.City', on_delete=models.CASCADE, null=True, related_name="zones")
    name = models.CharField(max_length=25)
    detour_index = models.DecimalField(max_digits=4, decimal_places=2)
    start = models.TimeField()
    end = models.TimeField()
    neighbors = models.ManyToManyField('self', symmetrical=False, blank=True, help_text="Each zone must have at leat one neighbour zone which is itself")
    # SRID 4326 is the standard for WGS84 (lat/lon)
    coords = models.JSONField(default=list)  # GeoJson format : [[exterior_coords], [hole_coords_1], [hole_coords_2], ...]
    is_active = models.BooleanField(default=False)
    objects = ObjectsManager()

    class Meta:
        unique_together = (('city', 'name'))

    # NOTE:: Initialize caching utility
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cached = CachedZone(self)  # Pass kitchen instance to KitchenCachable


    def __str__(self) -> str:
        return self.name
    
