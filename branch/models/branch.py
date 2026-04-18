import logging
import math
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from model_utils import FieldTracker
from branch.models.tag import Tag

from common.models.boundary.city import H3_BRANCH_RES
from common.models.boundary.zone import Zone
from core.managers import ObjectsManager
from core.utils import formattedError
from django.db.models import Count, Case, When, Q, F, Value, IntegerField, DurationField
from django.db.models.functions import Now, Coalesce
from django.core.cache import cache
import h3
from merchant.models.supplier import Supplier
from django.utils.functional import classproperty

logger = logging.getLogger(__name__)


class Branch(models.Model):
    class Status:
        open = "open"
        busy = "busy"
        closed = "closed"

        @classproperty
        def choices(cls):
            return ((cls.open, "Open"), (cls.busy, "Busy"), (cls.closed, "Closed"))

        @classproperty
        def values(cls):
            return tuple(v for v, _ in cls.choices)

    # NOTE:: Fields
    city = models.ForeignKey("common.City", on_delete=models.RESTRICT)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, db_index=True, related_name="branches")
    type = models.ForeignKey("common.Service", on_delete=models.RESTRICT, null=True)
    # Unique branch label, lowercase, max 30 chars, no spaces. Often administrative Zone based, and is public
    label = models.SlugField(
        max_length=20,
        validators=[MinLengthValidator(3), RegexValidator(regex=r"^[a-z0-9_-]+$")],
    )
    tags = models.ManyToManyField(Tag, related_name="branches", blank=True)  # optional, overrides supplier
    phone = models.CharField(max_length=15, help_text="Support contact")

    # Duration in minute
    ttr = models.DurationField("TTR")
    ept = models.DurationField("EPT")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.closed)
    # --- EPT delay ---
    delay_duration = models.DurationField("EPT delay", null=True, blank=True)
    delay_start = models.DateTimeField(null=True, blank=True)
    delay_reason = models.CharField(max_length=255, null=True, blank=True)

    # INFO:: Status

    # NOTE:: The platform should eensure uniformity accross branches of the same entity per city,
    # because accross city :
    # - customers expect a consistent experience,
    # - pricing and ordering rules are meant to be uniform across branches
    # Minimum order'subtotal amount required to place an order.
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    # --- Location ----
    lat = models.FloatField()
    lng = models.FloatField()
    h3_res8 = models.CharField(max_length=16, null=True, db_index=True)
    address = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, null=True, blank=True)
    pickup_instructions = models.CharField(max_length=255, null=True, blank=True)

    score = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tracker = FieldTracker(fields=["lat", "lng", "status"])
    objects = ObjectsManager()

    class Meta:
        ordering = (
            "-is_active",
            "city",
            "supplier__name",
            "label",
        )
        unique_together = [("city", "supplier", "type", "label")]

    @property
    def cached(self):
        """
        Importing inside the method is a valid and common way to avoid circular imports in Python.
        No performance issue. The import runs only once and is cached in sys.modules. The overhead of calling the method is negligible.
        """
        from branch.cached.branch import CachedBranch

        return CachedBranch(self)

    @property
    def grid_disk(self, res=H3_BRANCH_RES):
        L = h3.average_hexagon_edge_length(res, unit="km")
        diameter = 2 * L
        # Distance remaining after the first cell's reach (L)
        # divided by the diameter of each subsequent layer
        k = math.ceil((self.city.branch_radius_km - L) / diameter)
        return h3.grid_disk(self.h3_res8, k)

    @property
    def cache_key_set(self):
        return f"branch_cache_key_set:{self.id}"

    @property
    def name(self):
        if self.supplier:
            return f"{self.supplier.name} > {self.label}"
        return f"Store > {self.label}"

    @property
    def currency(self):
        return self.city.currency

    @property
    def dial_code(self):
        return self.city.country.dial_code

    @property
    def tel(self):
        return f"+{self.dial_code}{self.phone.lstrip('0')}"

    @property
    def is_store(self):
        return self.supplier_id is None

    @property
    def is_kitchen(self):
        return self.supplier_id is not None

    def __str__(self):
        return self.name

    def clean(self) -> None:
        if self.phone:
            self.phone = self.phone.lstrip("0")

    def save(self, *args, **kwargs):
        self.clean()
        # > Update H3 index if location has changed
        if self.tracker.has_changed("lat") or self.tracker.has_changed("lng"):
            self.h3_res8 = h3.latlng_to_cell(self.lat, self.lng, 8)
        super().save(*args, **kwargs)
