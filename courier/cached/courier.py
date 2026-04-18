from typing import TYPE_CHECKING
from datetime import date, datetime, timedelta
import logging
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Q, F, When, Case, IntegerField, Value, DurationField
from django.db.models.functions import Coalesce, Now, Greatest
from django.db.models.query import QuerySet
from common.models.boundary.city import City
from core.utils import formattedError
from courier.models.courier import Courier
from django.utils import timezone
import pytz

from courier.models.shift import CourierShift
from order.models.order import Order
from order.serializers.order import OrderSrz

logger = logging.getLogger(__name__)

# if TYPE_CHECKING:
#     from common.models.boundary.city import City


class CachedCourier:
    logger = logging.getLogger(__name__)

    class Keys:
        def __init__(self, courier: Courier):
            self.base = f"courier::{courier.id}"

        def active_orders(self):
            return f"{self.base}::active-orders"

        def active_shift(self):
            return f"{self.base}::active-shift"

        def shifts(self, dt: datetime):
            return f"{self.base}::shifts::{dt.strftime('%Y-%m-%d')}"

    def __init__(self, courier: Courier) -> None:
        self.courier = courier
        self.keys = self.Keys(courier)

    def active_orders(self) -> QuerySet:
        key = self.keys.active_orders()

        # try:
        #     cached = cache.get(key)
        #     if cached:
        #         return cached
        # except Exception as e:
        #     logger.warning(formattedError(e))

        allowed_statuses = [Order.Status.accepted, Order.Status.ready, Order.Status.picked_up]
        qs = (
            Order.objects.filter(courier=self.courier, status__in=allowed_statuses)
            .annotate(
                urgency_score=Case(
                    When(placed_at__lt=Now() - F("ept"), then=Value(3)),
                    When(status=Order.Status.accepted, then=Value(2)),
                    When(status=Order.Status.ready, then=Value(1)),
                    When(status=Order.Status.picked_up, then=Value(0)),
                    output_field=IntegerField(),
                ),
                time_in_status=Case(
                    When(
                        status=Order.Status.ready,
                        then=Now() - Coalesce(F("accepted_at"), F("placed_at")),
                    ),
                    When(
                        status=Order.Status.ready,
                        then=Now() - Coalesce(F("ready_at"), F("placed_at")),
                    ),
                    When(
                        status=Order.Status.picked_up,
                        then=Now() - Coalesce(F("pickedup_at"), F("placed_at")),
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
        payload = OrderSrz.Courier.listTile(qs)
        cache.set(key, payload, timeout=15 * 60)
        return payload

    def shifts(self, dt: datetime):
        key = self.keys.shifts(dt)
        try:
            cached = cache.get(key)
            if isinstance(cached, QuerySet):
                return cached
        except:
            cache.delete(key)
        yesterday = timezone.now().date() - timedelta(days=1)
        qs = (
            CourierShift.objects.filter(courier=self.courier, start__date=dt.date())
            .select_related("courier", "zone")
            .prefetch_related("slots")
        )
        cache.set(key, qs, timedelta(hours=1).total_seconds())
        return qs
