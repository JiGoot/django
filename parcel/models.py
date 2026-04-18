from datetime import datetime
from typing import Optional, Union
from django.db import models
from branch.models.branch import Branch

from core.utils import Currency, DialCode, get_random_code, get_random_pin
from courier.models.courier import Courier
from customer.models.customer import Customer
from parcel.utils import ParcelUtils
from django.core.exceptions import ValidationError


"""
Parcel can exceed LxWxH dimensions but must not exceed 5kg in weight. 
And 👉 40 × 30 × 10 cm (≈ 12 liters) in volume.
If it does , courier can visually verify and has the right to cancel the request.

For JiGoot Express / on-demand delivery service:
- Customer can schedule pickup.
- Drop-off is ASAP, never scheduled by customer.
- ETA is only computed after pickup.
- Prior to pickup, ETA displayed value is "Today · ASAP"


If "someone else" checkbox is not checked, according to the request type (send /receive) the sender or receiver info 
must be auto-filled with the requester's information.

"""


# Create your models here.
class Parcel(models.Model):
    """Parcel/delivery service model"""

    # Customer is the requester (owner)
    requester = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, related_name="parcels")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, related_name="parcels")

    # Who hands over the parcel
    sender_name = models.CharField(max_length=255, null=True, blank=True)
    sender_dial_code = models.CharField(max_length=10, choices=DialCode.choices, null=True, blank=True)
    sender_phone = models.CharField(max_length=15, null=True, blank=True)
    sender_email = models.EmailField(max_length=255, null=True, blank=True)

    # Who receives the parcel
    receiver_name = models.CharField(max_length=255, null=True, blank=True)
    receiver_dial_code = models.CharField(max_length=10, choices=DialCode.choices, null=True, blank=True)
    receiver_phone = models.CharField(max_length=50, null=True, blank=True)
    receiver_email = models.EmailField(max_length=255, null=True, blank=True)

    # Courier assignment
    courier = models.ForeignKey(
        Courier, on_delete=models.SET_NULL, null=True, blank=True, related_name="parcels"
    ) 
    # Responsible for delivery from custody
    custody_courier = models.ForeignKey(
        Courier, null=True, blank=True, on_delete=models.SET_NULL, related_name="custody_parcels"
    )

    # Parcel details
    type = models.CharField(max_length=20, choices=ParcelUtils.Type.choices)
    description = models.TextField(blank=True)
    is_fragile = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=ParcelUtils.Status.choices)

    # Security
    code = models.CharField(max_length=10, null=True, editable=False)
    pin = models.CharField(max_length=6, null=True, editable=False)

    # --- Pickup locations ---
    pickup_lat = models.FloatField(null=True, blank=True)
    pickup_lng = models.FloatField(null=True, blank=True)
    pickup_address = models.CharField(max_length=255, null=True, blank=True)
    pickup_landmark = models.CharField(max_length=255, null=True, blank=True)
    pickup_courier_instructions = models.CharField(max_length=255, null=True, blank=True)

    # --- Dropoff locations ---
    dropoff_lat = models.FloatField(null=True, blank=True)
    dropoff_lng = models.FloatField(null=True, blank=True)
    dropoff_address = models.CharField(max_length=255, null=True, blank=True)
    dropoff_landmark = models.CharField(max_length=255, null=True, blank=True)
    dropoff_courier_instructions = models.CharField(max_length=255, null=True, blank=True)

    # --- Custody details ---
    # For express delivery, if receiver is not available, custody location will be used
    # Parcel will be stored for a maximum of 24 hours to be picked up.
    custody_lat = models.FloatField(null=True, blank=True)
    custody_lng = models.FloatField(null=True, blank=True)
    custody_address = models.CharField(max_length=255, blank=True)
    custody_landmark = models.CharField(max_length=255, blank=True)

    # Scheduling
    pickup_date = models.DateField(null=True, blank=True)
    pickup_slot_start = models.TimeField(null=True, blank=True)
    pickup_slot_end = models.TimeField(null=True, blank=True)

    # Pricing
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Fee for insurance protection
    protection_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    currency = models.CharField(max_length=3, choices=Currency.choices, editable=False)

    # Timestamps
    placed_at = models.DateTimeField(auto_now_add=True)
    pickedup_at = models.DateTimeField(null=True, blank=True)
    custody_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Cancellation details
    cancelled_by = models.CharField(
        max_length=20, choices=ParcelUtils.CancelledBy.choices, null=True, blank=True
    )
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-placed_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        pickup_date__isnull=True, pickup_slot_start__isnull=True, pickup_slot_end__isnull=True
                    )
                    | models.Q(
                        pickup_date__isnull=False,
                        pickup_slot_start__isnull=False,
                        pickup_slot_end__isnull=False,
                    )
                ),
                name="schedule_pickup_all_or_none",
            )
        ]

    @property
    def total(self) -> float:
        """Calculate total cost of the parcel delivery"""
        return self.service_fee + self.protection_fee + self.delivery_fee

    @property
    def terminated(self) -> bool:
        return [ParcelUtils.Status.cancelled, ParcelUtils.Status.delivered].__contains__(self.status)

    @property
    def updated_at(self) -> Optional[datetime]:
        dates = [self.placed_at, self.pickedup_at, self.custody_at, self.delivered_at, self.cancelled_at]
        # Filter out None and return the latest
        return max(d for d in dates if d is not None)

    def __str__(self):
        return f"Parcel {self.code} - {self.type} - {self.status}"

    def clean(self):
        if sum(bool(x) for x in [self.sender_email, self.receiver_email]) != 1:
            raise ValidationError(
                "Exactly one of sender or receiver must be set. Which correspond to the requester's email."
            )
        # Validate pickup scheduling
        fields = [self.pickup_date, self.pickup_slot_start, self.pickup_slot_end]
        all_none = all(f is None for f in fields)
        all_set = all(f is not None for f in fields)
        if not (all_none or all_set):
            raise ValidationError(
                "pickup_date, pickup_slot_start, and pickup_slot_end must either all be set or all be null."
            )

    def save(self, *args, **kwargs):
        self.clean()
        if not self.code:
            self.code = get_random_code()
        if not self.pin:
            self.pin = get_random_pin(6)
        super().save(*args, **kwargs)
