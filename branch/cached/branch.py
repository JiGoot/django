from typing import TYPE_CHECKING
from datetime import date, timedelta
import logging
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Q, F, When, Case, IntegerField, Value, DurationField
from django.db.models.functions import Coalesce, Now, Greatest
from django.db.models.query import QuerySet
from branch.models.branch import Branch
from branch.models.variant import BranchVariant
from common.models.boundary.city import City
from common.models.catalog.category import Category
from common.serializers.category import CategorySrz
from core.utils import formattedError
from courier.models.courier import Courier
from django.utils import timezone
import pytz

from courier.models.shift import CourierShift
from order.models.order import Order
from django.db.models import Prefetch

from order.serializers.order import OrderSrz

logger = logging.getLogger(__name__)

# if TYPE_CHECKING:
#     from common.models.boundary.city import City


class CachedBranch:
    logger = logging.getLogger(__name__)

    class Keys:
        def __init__(self, branch: Branch):
            self.base = f"branch::{branch.id}"
            self.active_categories = f"{self.base}:active_categories"

        def active_orders(self):
            return f"{self.base}::active-orders"

    def __init__(self, branch: Branch) -> None:
        self.instance = branch
        self.keys = self.Keys(branch)

    @property
    def active_categories(self):
        """
        Invalidate on:
            Branch status changes
        """
        key = self.keys.active_categories
        try:
            cached = cache.get(key)
            if cached:
                return cached
        except Exception as e:
            logger.warning(formattedError(e))

        # TODO:: Make it optimal
        # Get the Categories with subcategories containing branch variants
        # Parents are filtered correctly
        # Only relevant subcategories are prefetched
        # No empty children
        subcategories_qs = Category.objects.filter(
            supplier_variants__branch_variants__branch=self.instance,
            supplier_variants__branch_variants__is_active=True,
        ).distinct()

        qs = (
            Category.objects.filter(
                parent__isnull=True,
                is_active=True,
                subcategories__supplier_variants__branch_variants__branch=self.instance,
            )
            .prefetch_related(Prefetch("subcategories", queryset=subcategories_qs))
            .distinct()
            .order_by("index")
        )

        payload = CategorySrz.default(qs)
        cache.set(key, payload, timeout=5 * 60)
        return payload

    @property
    def active_categories_preview(self):
        """
        Invalidate on:
            Branch status changes
        """
        key = self.keys.active_categories
        try:
            cached = cache.get(key)
            if cached:
                return cached
        except Exception as e:
            logger.warning(formattedError(e))
        from django.db.models import F, Window
        from django.db.models.functions import RowNumber

        active_category_ids = tuple(c["id"] for c in self.active_categories)

        BranchVariant.objects.filter(
            branch=self.instance,
            supplier_variant__category_id__in=active_category_ids,
            is_available=True,
        ).annotate(
            row_number=Window(
                expression=RowNumber(),
                partition_by=[F("category_id")],
                order_by=F("popularity_score").desc(),
            )
        ).filter(
            row_number__lte=12
        )

        qs = (
            BranchVariant.objects.select_related(
                "supplier_variant",
                "supplier_variant__variant",
                "supplier_variant__variant__item",
            )
            .filter(
                branch=self.instance,
                is_available=True,
                supplier_variant__is_available=True,
                supplier_variant__item__categoryitem__is_available=True,
                supplier_variant__item__categoryitem__category__branchcategory__branch=self.instance,
                supplier_variant__item__categoryitem__category__branchcategory__is_available=True,
            )
            .annotate(
                category_id=F("variant__item__categoryitem__category_id"),
                row_number=Window(
                    expression=RowNumber(),
                    partition_by=[F("variant__item__categoryitem__category_id")],
                    order_by=F("popularity_score").desc(),
                ),
            )
            .filter(row_number__lte=12)
            .order_by("category_id", "-popularity_score")
        )
        payload = CategorySrz.default(qs)
        cache.set(key, payload, timeout=5 * 60)
        return payload

    def active_orders(self) -> QuerySet:
        key = self.keys.active_orders()
        """Handle cache"""
        try:
            cached = cache.get(key)
            if cached:
                return cached
        except Exception as e:
            logger.warning(formattedError(e))

        """Compute"""
        allowed_statuses = [Order.Status.placed, Order.Status.accepted, Order.Status.ready]
        qs = (
            Order.objects.filter(branch=self.instance, status__in=allowed_statuses)
            .annotate(
                urgency_score=Case(
                    When(placed_at__lt=Now() - F("ept"), then=Value(3)),
                    When(status="placed", then=Value(2)),
                    When(status="accepted", then=Value(1)),
                    When(status="ready", then=Value(0)),
                    output_field=IntegerField(),
                ),
                time_in_status=Case(
                    When(status="placed", then=Now() - F("placed_at")),
                    When(
                        status="accepted",
                        then=Now() - Coalesce(F("accepted_at"), F("placed_at")),
                    ),
                    When(
                        status="ready",
                        then=Now() - Coalesce(F("ready_at"), F("placed_at")),
                    ),
                    output_field=DurationField(),
                ),
                updated_at=Greatest(
                    "placed_at",
                    "accepted_at",
                    "ready_at",
                    "pickedup_at",
                    "delivered_at",
                    "cancelled_at",
                ),
            )
            .order_by("-urgency_score", "time_in_status")
        )
        payload = OrderSrz.Branch.listTile(qs)
        cache.set(key, payload, timeout=5 * 60)
        return payload
