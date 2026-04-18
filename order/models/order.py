from datetime import datetime, timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from branch.models.branch import Branch
from branch.models.delivery_type import DeliveryType
from core.utils import CommissionType, Currency, DebitType, get_random_code, get_random_pin, haversine
import logging
from django.db import transaction
from django.db import models
from core.managers import ObjectsManager
from courier.models.courier import Courier
from customer.models.customer import Customer
from customer.models.payment import Payment
from django.utils.functional import classproperty
from wallet.models.wallet import Wallet
from typing import Optional, Union

logger = logging.getLogger(__name__)

# related_name='orders'

"""
In this design, Order is the universal transaction or “container” that represents a single customer request, regardless of branch type.
"""


class Order(models.Model):
    class Status:
        # NOTE:: Store order are automatically accepted when placed
        # cause they relay on stock
        placed = "placed"
        accepted = "accepted"
        ready = "ready"
        picked_up = "picked-up"
        on_the_way = "on-the-way"
        delivered = "delivered"
        cancelled = "cancelled"

        @classproperty
        def choices(cls):
            return (
                (cls.placed, "Placed"),
                (cls.accepted, "Accepted"),
                (cls.ready, "Ready"),
                (cls.picked_up, "Picked up"),
                (cls.on_the_way, "On the way"),
                (cls.delivered, "Delivered"),
                (cls.cancelled, "Cancelled"),
            )

        @classproperty
        def values(cls):
            return tuple(v for v, _ in cls.choices)

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, editable=False, related_name="orders")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, editable=False, related_name="orders")
    courier = models.ForeignKey(
        Courier, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    delivery_type = models.ForeignKey(DeliveryType, on_delete=models.RESTRICT,null=True, related_name="orders")    

    # === STATUS & TIMING ===
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.placed)
    # Estimated Prep-Time
    ept = models.DurationField("EPT", help_text="In duration")

    # --- Dropoff locations ---
    dropoff_lat = models.FloatField()
    dropoff_lng = models.FloatField()
    dropoff_address = models.CharField(max_length=255, editable=False)
    dropoff_landmark = models.CharField(max_length=255, null=True, blank=True, editable=False)
    dropoff_courier_instructions = models.CharField(max_length=255, null=True, blank=True)

    # Drop-off Scheduled
    dropoff_date = models.DateField(null=True, blank=True)
    dropoff_slot_start = models.TimeField(null=True, blank=True)
    dropoff_slot_end = models.TimeField(null=True, blank=True)



    # === PAYMENT & FEES ===
    is_prepaid = models.BooleanField(null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    small_order_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    cash_rounding_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    currency = models.CharField(max_length=3, choices=Currency.choices, editable=False)

    # Security
    code = models.CharField(max_length=10, null=True, editable=False)
    pin = models.CharField(max_length=6, null=True, editable=False)

    allow_substitution = models.BooleanField(default=True)

    # Store commission on the order at creation time from branch Supplier commission
    # Never compute commission from Supplier later.
    # Always freeze it.
    commission_type = models.CharField(max_length=50, choices=CommissionType.choices, null=True)
    commission_value = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    commission_value = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # === DATETIMES ===
    placed_at = models.DateTimeField(auto_now_add=True, editable=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    pickedup_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    objects = ObjectsManager()

    class Meta:
        ordering = ["-placed_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        dropoff_date__isnull=True,
                        dropoff_slot_start__isnull=True,
                        dropoff_slot_end__isnull=True,
                    )
                    | models.Q(
                        dropoff_date__isnull=False,
                        dropoff_slot_start__isnull=False,
                        dropoff_slot_end__isnull=False,
                    )
                ),
                name="order_schedule_dropoff_all_or_none",
            )
        ]

        # indexes = [
        #     models.Index(fields=["status", "placed_at"]),  # composite index
        # ]

    @property
    def type(self) -> str:
        return self.branch.type

    @property
    def total(self) -> float:
        return self.subtotal + self.small_order_fee + self.delivery_fee

    @property
    def terminated(self) -> bool:
        return [self.Status.cancelled, self.Status.delivered].__contains__(self.status)

    @property
    def eat(self) -> datetime:
        dist_km = haversine(self.branch.lat, self.branch.lng, self.lat, self.lng)  # in km
        avg_speed_kmh = 22  # in km/h
        travel_min = (dist_km / avg_speed_kmh) * 60  # avg speed 22km/h
        buffer_min = dist_km * 1  # 1 min per km
        return self.pickedup_at + timedelta(minutes=travel_min + buffer_min)

    # @property
    # def updated_at(self) -> datetime:
    #     dates = [
    #         self.placed_at,
    #         self.accepted_at,
    #         self.ready_at,
    #         self.pickedup_at,
    #         self.delivered_at,
    #         self.cancelled_at,
    #     ]
    #     # Filter out None and return the latest
    #     return max(d for d in dates if d is not None)

    @property
    def payment_status(self) -> Optional[Union[str, float]]:
        """
        Returns tuple of (status, remaining_amount)
        - status: 'pending' if payment needed, 'paid' if fully paid
        - remaining_amount: None if fully paid, otherwise Decimal amount due
        """
        total_paid = self.payments.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")
        # Payment.objects.filter(order_type=BranchType.store, order_id=self.id)
        # self.store_payments
        # .aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

        remaining = max((Decimal(self.total) - total_paid), Decimal("0.00"))
        return (Payment.Status.pending, remaining) if remaining > 0 else (Payment.Status.paid, 0)

    def __str__(self):
        return self.code

    def mark_as_paid(self):
        payment_status, remaining = self.payment_status
        if payment_status == Payment.Status.paid and remaining is None:
            raise ValueError("Order already Paid")
        if remaining and remaining > 0:
            with transaction.atomic():
                # INFO:: Create payment record
                Payment.objects.create(
                    customer=self.customer,
                    store_order=self,
                    method=Payment.Methods.cash,
                    amount=remaining,
                    currency=self.currency,
                    reference=None,
                    aggregator=None,
                )

    def mark_as_droppedoff(self):
        # INFO:: Validate pre-conditions
        if self.terminated:
            raise ValueError("Terminated order cannot mark as delivered")

        payment_status, remaining = self.payment_status
        if payment_status != Payment.Status.paid or remaining is not None:
            raise ValueError("Payment is pending")

        with transaction.atomic():  # Ensure all operations succeed or fail together
            # INFO:: Update order status
            # TODO:: Ensure that all the kitchen credit for this order does not exceed
            # the order subtotal
            self.status = self.Status.delivered
            self.delivered_at = timezone.now()
            self.save(update_fields=["status", "delivered_at"])

            # INFO:: Credit courier wallet (75% of delivery fee)
            if self.courier:
                courier_wallet, _ = Wallet.objects.get_or_create(courier=self.courier)
                courier_earning = self.delivery_fee * 0.75
                courier_wallet.credit(
                    amount=courier_earning,
                    order_type=self.type,
                    order_id=self.pk,
                )
                # Handle COD debt if remaining amount exists during delivery
                # Courier will have to settle their debt in one of the store locaion
                if remaining and remaining > 0:
                    courier_wallet.debit(
                        type=DebitType.debt,
                        amount=remaining,
                        order_type=self.type,
                        order_id=self.pk,
                    )

    def recalculate_subtotal(self):
        """NOTE::  Subtotal exclude the removed Item"""
        # TODO If the subtotal is ajusted we should also ajust the delivery fee accordingly,
        # specially the subtotal portion of the delivery fee
        subtotal = 0
        for item in self.items.filter(removed=False):
            subtotal += item.price * item.qty
        return subtotal

    def clean(self) -> None:
        # Validate pickup scheduling
        fields = [self.dropoff_date, self.dropoff_slot_start, self.dropoff_slot_end]
        all_none = all(f is None for f in fields)
        all_set = all(f is not None for f in fields)
        if not (all_none or all_set):
            raise ValidationError(
                "dropoff_date, dropoff_slot_start, and dropoff_slot_end must either all be set or all be null."
            )
        #     match self.status:
        #         case Order.Status.ready:
        #             if self.ready_at is None:
        #                 self.ready_at = timezone.now()
        #         case Order.Status.picked_up:
        #             if self.pickedup_at is None:
        #                 self.pickedup_at = timezone.now()
        #         case Order.Status.delivered:
        #             if self.delivered_at is None:
        #                 self.delivered_at = timezone.now()
        #             _pstatus, _pamount = self.payment_status
        #             if _pamount is not None:
        #                 raise ValidationError(
        #                     f"payment of {_pamount} {self.store.currency.upper()}  is required", code='invalide')
        return super().clean()

    def save(self, *args, **kwargs) -> None:
        # INFO:: Ensure exactly one branch is set
        if not self.code:
            self.code = get_random_code()
        if not self.pin:
            self.pin = get_random_pin()
        return super().save(*args, **kwargs)
