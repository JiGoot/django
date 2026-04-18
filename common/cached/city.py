from typing import TYPE_CHECKING
from datetime import date, timedelta
import logging
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Q
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from affiche.models import Affiche
from branch.models.branch import Branch
from branch.models.delivery_type import DeliveryType
from branch.models.shift import Shift
from common.models.boundary.city import H3_BRANCH_RES, City
from common.models.boundary.zone import Zone
from django.db.models import Case, When, Value, BooleanField, IntegerField
from django.db.models import Exists, OuterRef, Window, F, Prefetch
from django.db.models.functions import RowNumber
from django.core.paginator import Page, Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import Greatest, Least, ACos, Cos, Radians, Sin, Floor
from django.utils import timezone
import pytz, h3

from common.serializers.vertical_type import ServiceSrz

logger = logging.getLogger(__name__)

# if TYPE_CHECKING:
#     from common.models.boundary.city import City


class CachedCity:
    logger = logging.getLogger(__name__)

    class Key:
        def __init__(self, city: City):
            base = f"city-{city.id}"
            self.version = cache.get_or_set(f"{base}:version", 1, timeout=timedelta(days=1).total_seconds())
            self.affiches = f"{base}:affiches"
            self.active_shift = f"{base}:active-shift"
            self.branches = f"{base}:v{self.version}:branches"
            self.vertical_types = f"{base}:vertical-types"
            self.zones = f"{base}:zones"

        # >> Caching keys for [nearby] branches
        def nearest_branches(self, h3_cell, type: str, page=1, tags=None):
            if tags:
                return f"{h3_cell}:branches:{type}:{tags}:{page}"
            return f"{h3_cell}:branches:{type}:{page}"

    def __init__(self, city: "City") -> None:
        self.city = city
        self.keys = self.Key(city)

    @property
    def affiches(self) -> QuerySet:
        """Retrieve affiches for the city or query and cache them"""
        try:
            cached = cache.get(self.keys.affiches)
            if isinstance(cached, QuerySet):
                return cached
        except:
            cache.delete(self.keys.affiches)
        tz = pytz.timezone(self.city.timezone)  # e.g. "Africa/Kinshasa"
        local_now = timezone.now().astimezone(tz)
        qs = Affiche.objects.filter(
            Q(is_active=True),
            Q(Q(start__lte=local_now, end__gte=local_now) | Q(start__isnull=True, end__isnull=True)),
        )[:4]
        cache.set(self.keys.affiches, qs, timeout=timedelta(minutes=15).total_seconds())
        return qs

    def nearest_branches(
        self,
        typeId: int,
        lat: float,
        lng: float,
        ring_step_km: float = 0.5,
        page_id=None,
        tags=None,
    ) -> Page:
        """Get nearest branches for a given h3 cell of resolution 8 and an optional list of tags
        result is ordered by various criteria placing all closed branches at the bottom"""

        # VALIDATION::
        # Add input validation
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            raise ValueError("Invalid coordinates")

        if tags:
            tags = sorted(tags)

        # Get the target H3 cell
        target_cell = h3.latlng_to_cell(lat, lng, H3_BRANCH_RES)
        key = self.keys.nearest_branches(target_cell, typeId, page_id, tags)
        # Try to get nearest branches from cache
        # try:
        #     cached = cache.get(key)
        #     return cached
        # except:
        #     cache.delete(key)

        # Fetch neighboring kitchens
        #
        tz = pytz.timezone(self.city.timezone)  # e.g. "Africa/Kinshasa"
        local_now = timezone.now().astimezone(tz)

        # > Precomputing ring distance, Map cells by k-ring
        cells = {}
        seen = set()
        # For food delivery, 3 km is usually the operational max.
        for k in range(4):  # 0...3,  k=3 → ~3 km coverage (depending on resolution)
            for cell in set(h3.grid_disk(target_cell, k)) - seen:
                cells[cell] = k
            seen |= set(cells)

        # Get customer default service grid for the given city.
        service_grid = h3.grid_disk(target_cell, self.city.k_ring)
        # Standard Haversine constant (Earth's radius in km)
        R = 6371.0
        qs = (
            Branch.objects.filter(
                Q(delivery_types__code="asap", h3_res8__in=service_grid) | ~Q(delivery_types__code="asap"),
                city=self.city,
                type__id=typeId,
                is_active=True,
            )
            .filter(Q(supplier__is_active=True) | Q(supplier__isnull=True))
            .select_related("supplier", "supplier__country")
            .prefetch_related(
                Prefetch(
                    "delivery_types",  # the related name on Branch
                    queryset=DeliveryType.objects.filter(is_active=True),
                    to_attr="active_delivery_types",  # optional: store in a custom attribute
                ),
                Prefetch(
                    "shifts",  # the related name on Branch
                    queryset=Shift.objects.filter(
                        weekdays__contains=[local_now.isoweekday()],
                        is_active=True,
                    ),
                    to_attr="active_shifts",  # optional: store in a custom attribute
                ),
            )
        )

        if tags:
            qs = qs.filter(supplier__tags__id__in=tags).annotate(
                matches=Count("supplier__tags", filter=Q(supplier__tags__id__in=tags))
            )
        asap = DeliveryType.objects.filter(
            branch=OuterRef("pk"),
            code="asap",
            is_active=True,
        )

        qs = qs.annotate(
            # NOTE:: In client UI disable ASAP option for branches that are outside the customer's service grid, even if they have ASAP delivery type.
            # ASAP + next_day	- outside grid -	False
            # ASAP + next_day	inside grid	- True
            has_asap=Case(
                When(Exists(asap) & Q(h3_res8__in=service_grid), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
            has_shift=Exists(  # Subquery to check if there is a matching shift for the current time and weekday
                Shift.objects.filter(
                    branch=OuterRef("pk"),  # Correlate with the outer Branch query
                    weekdays__contains=[local_now.isoweekday()],
                    is_active=True,
                )
            ),
            is_closed=Case(
                When(status=Branch.Status.closed, then=Value(True)),
                When(
                    Q(has_shift=True) & ~Q(status=Branch.Status.closed),
                    then=Value(False),
                ),
                default=Value(True),
                output_field=BooleanField(),
            ),
            k_ring=Case(
                *[When(h3_res8=cell, then=k) for cell, k in cells.items()],
                output_field=IntegerField(),
            ),
            # ACos() can crash if the inner value becomes 1.0000000002 or -1.0000000001 due to floating precision.
            # We clamp the cosine expression to [-1, 1] inside SQL.
            # Wrap the inner expression with Least() and Greatest()
            distance=R
            * ACos(
                Greatest(
                    Value(-1.0),
                    Least(
                        Value(1.0),
                        Cos(Radians(lat)) * Cos(Radians(F("lat"))) * Cos(Radians(F("lng")) - Radians(lng))
                        + Sin(Radians(lat)) * Sin(Radians(F("lat"))),
                    ),
                )
            ),
            radial_step=Floor(F("distance") / ring_step_km, output_field=IntegerField()),
        )

        ranking_order = [F("is_closed").asc()]  # False (open) first
        if tags:
            ranking_order.append(F("matches").desc())  # more tag matches first (if tags are provided)

        ranking_order += [
            F("k_ring").asc(),  # closest k-ring
            F("radial_step").asc(),  # closer branches first
        ]
        qs = qs.annotate(
            rank_by_supplier=Window(
                expression=RowNumber(), partition_by=[F("supplier"), F("type")], order_by=ranking_order
            )
        ).filter(rank_by_supplier=1)

        # Final ordering: open branches first, then by tag matches (if tags), then by k-ring, then by radial step
        qs = qs.order_by(
            *[
                "is_closed",
                *(["-matches"] if tags else []),
                "k_ring",
                "radial_step",
            ]
        )

        # NOTE ----- Pagination -----
        # paginator = Paginator(qs, 25)
        # try:
        #     page = paginator.page(page_id)
        # except (EmptyPage, PageNotAnInteger):
        #     # make an empty page with the requested page number
        #     page = Page([], page_id, paginator)

        cache.set(key, qs, timedelta(minutes=15).total_seconds())
        return qs

    @property
    def vertical_types(self) -> dict:
        """Retrieve vertical types for the city or query and cache them"""
        key = self.keys.vertical_types
        # try:
        #     return cache.get(key)
        # except:
        #     cache.delete(key)

        payload = {
            "branches": ServiceSrz.default(self.city.branch_types.filter(is_active=True)),
            "services": ServiceSrz.default(self.city.services.filter(is_active=True)),
        }
        cache.set(key, payload, timeout=timedelta(minutes=30).total_seconds())
        return payload

    # @property
    # def active_shift(self):
    #     key = self.keys.active_shift
    #     try:
    #         cached = cache.get(key)
    #         if isinstance(cached, QuerySet):
    #             return cached
    #     except:
    #         cache.delete(key)
    #     current_weekday = timezone.now().isoweekday()
    #     current_time = timezone.now().time()
    #     active_shift = self.shifts.filter(
    #         weekdays__contains=[current_weekday],
    #         start_time__lte=current_time,
    #         end_time__gte=current_time,
    #     )
    #     cache.set(key, active_shift, timedelta(minutes=15).total_seconds())
    #     return active_shift

    @property
    def branches(self) -> QuerySet:
        try:
            cached = cache.get(self.keys.branches)
            if isinstance(cached, QuerySet):
                return cached
        except:
            cache.delete(self.keys.branches)

        qs = Branch.objects.filter(city=self.city, is_active=True).prefetch_related("shifts")
        cache.set(self.keys.branches, qs, timedelta(hours=1).total_seconds())
        return qs

    @property
    def zones(self) -> QuerySet:
        try:
            cached = cache.get(self.keys.zones)
            if isinstance(cached, QuerySet):
                return cached
        except:
            cache.delete(self.keys.zones)
        qs = Zone.objects.filter(city=self.city, is_active=True).prefetch_related("neighbors")
        cache.set(self.keys.zones, qs, timedelta(hours=1).total_seconds())
        return qs
