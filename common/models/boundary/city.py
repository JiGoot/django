import math
from django.utils.translation import gettext_lazy as _
from django.db import models

# from django.db.models import Extent


import logging
from datetime import timedelta
from django.db import models
from common.models.boundary.country import Country
from common.models.boundary.zone import Zone
from core.managers import ObjectsManager
from django.contrib.postgres.fields import ArrayField
import h3
from core.utils import Timezones

logger = logging.getLogger(__name__)

H3_BRANCH_RES = 8


class City(models.Model):
    """NOTE: Zone are their own neighbour first."""

    country = models.ForeignKey(Country, on_delete=models.RESTRICT)
    name = models.CharField(max_length=25)
    timezone = models.CharField(max_length=100, null=True, choices=Timezones.choices)
    # center
    lat = models.FloatField()
    lng = models.FloatField()

    services = models.ManyToManyField(
        'common.Service',
        through='common.CityService',
        related_name="cities",
        blank=True,
        help_text="Non-retail services available in this city (parcel, events, taxi, etc.)"
    )
    # NOTE This is the limit or minimum amount required for an order to avoid penalties
    small_order_threshold = models.DecimalField(max_digits=10, decimal_places=2)
    small_order_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # NOTE: Service fee
    service_fee_rate = models.DecimalField(max_digits=10, decimal_places=2)
    service_fee_cap_amount = models.DecimalField(max_digits=10, decimal_places=2)
    # Default Branch operational radius in kilometers, used to determine the maximum distance for delivery and
    # to calculate delivery fees.
    service_radius = models.FloatField(default=3, help_text="in kilometers")

    # NOTE:: Delivery fee
    delivery_fee_base_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee_cap_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee_cpm = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee_cpk = models.DecimalField(max_digits=10, decimal_places=2)

    debt_cap = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=3000.00,
        help_text="Courier maximum dept",
    )
    # [bbox] In [min_lng, min_lat, max_lng, max_lat]:
    # min_lng, min_lat → southwest corner (bottom-left)
    # max_lng, max_lat → northeast corner (top-right)
    bbox = ArrayField(models.FloatField(), size=4, null=True)  # TODO:: To be removed
    objects = ObjectsManager()

    class Meta:
        verbose_name_plural = "Cities"  # INFO change default table name in admin panel
        unique_together = (
            "country",
            "name",
        )

    @property
    def cached(self):
        from common.cached.city import CachedCity
        return CachedCity(self)

    @property
    def k_ring(self):
        edge_length = h3.average_hexagon_edge_length(H3_BRANCH_RES, unit="km")
        diameter = 2 * edge_length
        return math.ceil((self.service_radius - edge_length) / diameter)

    @property
    def length(self):
        size = self.cached.zones
        return len(size) if size else None

    @property
    def country_code(self):
        return self.country.code

    @property
    def currency(self):
        return self.country.currency

    @property
    def smallest_bill(self):
        return self.country.smallest_bill

    def __str__(self) -> str:
        return f"{self.name} | {self.country.code}"

    def clean(self) -> None:
        self.name = self.name.lower() if self.name else self.name
        return super().clean()

    # NOTE:: ACTIONS METHODS
    def update_bbox(self):
        """
        Calculates the bounding box (bbox) for a list of Zone instances,
        where each zone.polygon is a GeoJSON-like list of rings (the first is the exterior).

        Args:
            zones (list): A list of Zone objects, where each zone.polygon
                        is a list of rings, like [[[lon1, lat1], ...], [[lon_hole1, lat_hole1], ...]].

        Returns:
            list: The bounding box as a list [min_lon, min_lat, max_lon, max_lat],
                or None if no valid coordinates are found.
        """
        zones = self.cached.zones
        if not zones:
            return None

        # Initialize with extreme values
        min_lon = float("inf")
        min_lat = float("inf")
        max_lon = float("-inf")
        max_lat = float("-inf")

        has_coords = False

        for zone in zones:
            if isinstance(zone, Zone):
                # Expected structure: [[exterior_coords], [hole_coords_1], [hole_coords_2], ...]
                polygon = zone.polygon

            # Skip if the polygon is empty or doesn't have an exterior ring
            if not polygon or not polygon[0]:
                continue

            # We only need the *exterior* boundary for the Bounding Box calculation.
            # This is the first element in the list of rings.
            exterior_coords = polygon[0]
            has_coords = True

            for lon, lat in exterior_coords:
                # Update min/max longitude (southwest)
                min_lon = min(min_lon, lon)
                max_lon = max(max_lon, lon)

                # Update min/max latitude (northeast)
                min_lat = min(min_lat, lat)
                max_lat = max(max_lat, lat)

        if not has_coords:
            return None

        # Return the bbox in the standard GeoJSON order: [min_lon, min_lat, max_lon, max_lat]
        return [min_lon, min_lat, max_lon, max_lat]




