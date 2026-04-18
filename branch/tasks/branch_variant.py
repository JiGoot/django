from typing import TYPE_CHECKING
from datetime import date, timedelta
import logging
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Sum, Q, F, When, Case, IntegerField, Value, DurationField
from django.db.models.functions import Coalesce, Now
from django.db.models.query import QuerySet
from branch.models.branch import Branch
from branch.models.variant import BranchVariant, BranchVariantDailySales
from common.models.boundary.city import City
from core.utils import formattedError
from courier.models.courier import Courier
from django.utils import timezone
import pytz

from courier.models.shift import CourierShift
from order.models.order import Order

logger = logging.getLogger(__name__)

# if TYPE_CHECKING:
#     from common.models.boundary.city import City


class BranchVariantCommand:
    logger = logging.getLogger(__name__)

    def __init__(self, branch_variant: BranchVariant) -> None:
        self.instance = branch_variant

    def increment_daily_sales(self, quantity):
        branch_tz = pytz.timezone(self.instance.branch.city.timezone)
        today = timezone.now().astimezone(branch_tz).date()
        # 1️⃣ Increment today's sales safely
        obj, _ = BranchVariantDailySales.objects.get_or_create(
            branch_variant=self.instance,
            date=today,
            defaults={"qty": 0},
        )

        BranchVariantDailySales.objects.filter(pk=obj.pk).update(qty=F("qty") + quantity)

    # def update_scores(self, quantity: int) -> QuerySet:
    #     branch_tz = pytz.timezone(self.instance.branch.city.timezone)
    #     today = timezone.now().astimezone(branch_tz).date()

    #     # 2️⃣ Aggregate last windows
    #     stats = BranchVariantDailySales.objects.filter(
    #         branch_variant=self, date__gte=today - timedelta(days=90)
    #     ).aggregate(
    #         sold_1d=Sum("qty", filter=Q(date=today)),
    #         sold_7d=Sum("qty", filter=Q(date__gte=today - timedelta(days=7))),
    #         sold_30d=Sum("qty", filter=Q(date__gte=today - timedelta(days=30))),
    #         sold_90d=Sum("qty", filter=Q(date__gte=today - timedelta(days=90))),
    #     )

    #     sold_1d = stats["sold_1d"] or 0
    #     sold_7d = stats["sold_7d"] or 0
    #     sold_30d = stats["sold_30d"] or 0
    #     sold_90d = stats["sold_90d"] or 0

    #     # 3️⃣ Compute scores
    #     popularity_score = (sold_90d * 0.3) + (sold_30d * 1.5) + (sold_7d * 3)
    #     trend_score = ((sold_1d * 4) + sold_7d) / (sold_30d + 1)

        # 4️⃣ Update BranchVariant (NOT DailySales)
        # obj.branch_variant.popularity_score = popularity_score
        # obj.branch_variant.trend_score = trend_score
        # obj.save(update_fields=["popularity_score", "trend_score"])

    def delete_old_daily_sales(self):
        today = timezone.localdate()
        self.branch_variant.daily_sales.filter(date__lt=today - timedelta(days=120)).delete()
