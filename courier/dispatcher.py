import logging

import pytz
from order.models.order import Order
from core.rabbitmq.broker import publisher
import datetime
import numpy as np
from scipy.optimize import linear_sum_assignment
from math import radians, sin, cos, sqrt, atan2
from django.utils import timezone
from django.db import transaction
from django.db import models
from common.models import City
from order.notify import OrderNotify
from core.utils import CourierStatus, geodesic_haversine
from courier.models import Courier, CourierShift
from courier.models.offer import CourierOffer, OfferStatus
from core.utils import DashStatus








ACTIVE_ORDER_STATUSES = [Order.Status.accepted, Order.Status.ready]


class CourierDispatcher:

    def __init__(self, city: City):
        self.city = city
        self.speed = 20  # [km/h]
        self.prob = None
        self.matches = []

    @staticmethod
    def start(id: int):
        # with transaction.atomic(): # ensuring only one worker processes a city dispatch at a time
        city = City.objects.get_or_none(id=id)
        assert city, "Dispatcher cannot be started, city not found!"
        dispatcher = CourierDispatcher(city)
        return dispatcher.dispatch()

    def get_couriers(self):
        """Get couriers with capacity who are actively working"""
        tz = pytz.timezone(self.city.timezone)  # e.g. "Africa/Kinshasa"
        local_now = timezone.now().astimezone(tz)

        # Statuses that count toward a courier's current load

        # Conditions for paused couriers to still be considered available
        PAUSED_CONDITIONS = (
            models.Q(status=Courier.Status.online)
            | models.Q(status=Courier.Status.paused, paused_start__isnull=True)
            | models.Q(
                status=Courier.Status.paused,
                paused_start__lte=self.now - datetime.timedelta(minutes=10),
            )
        )
        return (
            Courier.objects.annotate(
                load=models.Count(
                    "orders",
                    filter=models.Q(orders__status__in=ACTIVE_ORDER_STATUSES),
                    distinct=True,  # ← Avoid double-counting
                ),
                has_active_shift=models.Exists(
                    CourierShift.objects.filter(
                        courier=models.OuterRef("pk"),
                        status=DashStatus.confirmed,
                        date=local_now.isoweekday(),
                    )
                ),
            )
            .filter(
                city=self.city,
                is_active=True,
                load__lt=models.F("max_load"),
                has_active_shift=True,
                wallet__balance__lte=self.city.debt_cap * models.F("worthiness"),
            )
            .filter(PAUSED_CONDITIONS)
        )

    def get_orders(self):
        """Get all unassigned orders ready for dispatch"""
        orders = Order.objects.select_related("customer", "branch", "courier").filter(
            models.Q(
                courier__isnull=True,
                ready_at__lte=timezone.now(),
                status__in=ACTIVE_ORDER_STATUSES,
            ),
            store__city=self.city,
            kitchen__city=self.city,
        )

        return orders

    def cost_matrix(self, couriers, orders):
        """Create cost matrix for assignment problem"""
        # TODO:: add remaining preparation time
        matrix = np.zeros((len(couriers), len(orders)))
        for i, courier in enumerate(couriers):
            for j, order in enumerate(orders):

                # 1. Distance calculations
                pickup_dist = geodesic_haversine(courier.point, order.branch.point)
                delivery_dist = geodesic_haversine(order.branch.point, order.point)

                # 2. Courier total travel time components
                capacity_penalty = courier.load / courier.max_load
                load_factor = 1 + capacity_penalty * 0.3
                base_cost = (
                    (pickup_dist + delivery_dist) / courier.speed
                ) * load_factor

                # 3. Preparation time with late order handling
                ready_at = (
                    order.accepted_at + order.ept if order.accepted_at else self.now
                )
                remaining_prep_time = (ready_at - self.now).total_seconds() / 60
                prep_factor = 1 + (remaining_prep_time / 120)
                matrix[i][j] = base_cost * max(
                    0.1, min(prep_factor, 2.0)
                )  # Clamp to [0.1, 2.0]
        return matrix

    def dispatch(self):
        """Main dispatch method using Hungarian algorithm"""
        couriers = self.get_couriers()
        orders = self.get_orders()
        if not couriers and not orders:
            return logger.warning("No couriers or orders available")
        cost_matrix = self.cost_matrix(couriers, orders)

        # Solve assignment problem
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        # # Dynamic distance thresholds
        # max_distance = 8  # km
        # if self.now.hour in {7, 8, 9, 17, 18, 19}:  # Fixed set comparison
        #     max_distance = 5

        offers = []
        with transaction.atomic():
            for courier_idx, order_idx in zip(row_ind, col_ind):
                # Max distance threshold (km)
                # if cost_matrix[courier_idx][order_idx] < max_distance:
                courier: Courier = couriers[courier_idx]
                order: Order = orders[order_idx]

                # INFO:: Check order viability first
                if order.courier or order.terminated:
                    continue

                # INFO:: Get or create offer (no expiration checks)
                offer, created = CourierOffer.objects.get_or_create(
                    courier=courier, order=order
                )

                # INFO:: Skip if already resolved
                if offer.status in [OfferStatus.accepted, OfferStatus.rejected]:
                    continue

                # INFO:: Cooldown and reminder logic.
                # This send the reminder offer only after at least 3 min
                if not created and offer.status == OfferStatus.pending:
                    cooldown = datetime.timedelta(minutes=3)
                    if (timezone.now() - offer.notified_at) < cooldown:
                        continue
                    else:  # Refresh timestamp if cooldown passed
                        offer.notified_at = timezone.now()  # Refresh offer
                        offer.remider_count = offer.reminder_count + 1
                        offer.save(update_fields=["notified_at", "remider_count"])

                # INFO:: Send notification
                publisher.publish(
                    OrderNotify.Courier.new_offer,
                    courier.pk,
                    order.pk,
                )
                offers.append(offer)

            return couriers, orders, offers


logger = logging.getLogger(name=__file__)
