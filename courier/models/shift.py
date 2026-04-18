from typing import TYPE_CHECKING
from datetime import datetime, timedelta
import logging
from django.utils.translation import gettext_lazy as _
from django.db import models, transaction
from django.db.models import Q
import pytz
from common.models.boundary.zone import Zone
from common.models.slot import Slot
from core.managers import ObjectsManager
from django.utils import timezone
from core.utils import DashStatus
from rest_framework import exceptions

from django.core.exceptions import ValidationError
from core.utils import CourierStatus, Currency, DebitType, WalletType
from wallet.models.transaction import Transaction

# Create your models here.
logger = logging.getLogger(__file__)

if TYPE_CHECKING:
    from courier.models.courier import Courier


class CourierShift(models.Model):
    """
    CourierShift Model

    Purpose:
        Represents a courier's scheduled work period within the platform.
        Tracks the lifecycle of a shift from registration to completion, including pauses, activation, and cancellations.

    Use Cases:
        1. Couriers register for one or more sequential slots to define a shift.
        2. Shift start and end datetimes (`start_at`, `end_at`) are materialized from the **earliest start** and **latest end** of selected slots.
        3. Shift can be started only within a defined window around `start_at` (default: 10 min before to 15 min after).
        4. Couriers can pause/resume shifts, allowing flexible breaks while maintaining accountability.
        5. Customers or operations teams can query active, upcoming, or completed shifts for resource planning.
        6. System periodically marks shifts as `completed` once `end_at` has passed and the shift is still active.
        7. System periodically cancels shifts that were never started beyond the allowed late-start window.

    Fields:
        - `courier` (ForeignKey): Reference to the courier.
        - `zone` (ForeignKey): Starting zone where the shift must be activated for the first time, to distribute couriers across the city.
        - `slots` (ManyToManyField): Selected Slot(s) for this shift; slots must be sequential and connected to ensure uninterrupted flow.
        - `start_at` (DateTimeField): Materialized start datetime from earliest slot.
        - `end_at` (DateTimeField): Materialized end datetime from latest slot.
        - `status` (CharField): Shift lifecycle status: scheduled, active, paused, cancelled, completed.
        - `pause_count` (PositiveSmallIntegerField): Number of times courier paused the shift.
        - `last_paused_at` (DateTimeField): Timestamp of last pause.
        - `created_at` (DateTimeField): Timestamp of shift creation.
        - `activated_at` (DateTimeField): Timestamp when courier started the shift.
        - `cancelled_at` (DateTimeField): Timestamp when courier cancelled the shift.

    Lifecycle Statuses:
        - scheduled: Courier registered the shift but has not started it.
        - active: Shift started by courier.
        - paused: Shift temporarily paused by courier.
        - cancelled: Shift cancelled by courier before starting or during activation.
        - completed: Automatically set by periodic job after `end_at` has passed.

    Key Requirements:
        1. Simplicity: Minimal fields for essential tracking.
        2. Scalability: Handles many couriers and shifts efficiently; queries rely on indexed fields like (status, start_at, end_at).
        3. Traceability: All lifecycle events are timestamped for auditing, payout, and analytics.
        4. Sequential slots: Shifts must consist of connected, uninterrupted slots.
        5. Start window: Shift can only be activated 10 min before start_at to 15 min after start_at.
        6. Automatic completion: Periodic job sets `status = completed` when `end_at <= local_now` and `status == active`.
        7. Automatic cancellation: Periodic job cancels shifts not started beyond the allowed late-start window (`start_at + 15 min`).
        8. Materialized times: `start_at` and `end_at` computed at creation to simplify queries and reporting.
        9. Zone distribution: Initial activation zone ensures couriers are spread across city areas.

    Usage Examples:
        # Start a shift
        shift.start()

        # Pause and resume a shift
        shift.pause()
        shift.resume()

        # Cancel a shift
        shift.cancel()

        # Complete a shift (normally done by periodic job)
        shift.complete()

    Notes:
        - Couriers may register for multiple slots as long as they are available and sequential.
        - All operational logic (availability, customer assignment, payout) relies on `status` and materialized times.
        - Periodic jobs handle automatic status updates to keep the system consistent.
        - System should enforce slot continuity when creating shifts: no gaps allowed between assigned slots.
    """

    courier = models.ForeignKey("courier.Courier", on_delete=models.CASCADE, related_name="shifts")
    # Starting zone, where the shift must be activated for the first time
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="shifts")
    slots = models.ManyToManyField(Slot, related_name="shifts")
    is_dash = models.BooleanField(default=False)
    # Materialized datetimes (computed from selected slots)
    start = models.DateTimeField()
    end = models.DateTimeField()

    status = models.CharField(
        max_length=16,
        choices=DashStatus.choices,
        default=DashStatus.scheduled,
        db_index=True,
    )
    pause_count = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    objects = ObjectsManager()

    class Meta:
        verbose_name = "Shift"
        verbose_name_plural = "Shifts"
        ordering = ("-start", "end")
        indexes = [
            models.Index(fields=["courier", "status"]),
            models.Index(fields=["start", "end"]),
        ]

    # def start(self):
    #     self.status = DashStatus.active
    #     self.activated_at = timezone.now()
    #     self.save(update_fields=["status", "activated_at"])

    # def pause(self):
    #     self.status = DashStatus.paused
    #     self.last_paused_at = timezone.now()
    #     self.pause_count += 1
    #     self.save(update_fields=["status", "last_paused_at", "pause_count"])

    # def resume(self):
    #     self.status = DashStatus.active
    #     self.save(update_fields=["status"])

    # def complete(self):
    #     self.status = DashStatus.completed
    #     self.save(update_fields=["status"])

    # def cancel(self):
    #     self.status = DashStatus.cancelled
    #     self.cancelled_at = timezone.now()
    #     self.save(update_fields=["status", "cancelled_at"])

    @property
    def is_active(self):
        utc_now = datetime.utcnow()
        utc_now = utc_now.replace(tzinfo=pytz.utc)
        tz = pytz.timezone(self.courier.city.timezone)  # e.g. "Africa/Kinshasa"
        local_now = timezone.now().astimezone(tz)
        if (
            self.status == DashStatus.completed
            and self.start <= local_now.time()
            and self.end >= local_now.time()
        ):
            return True
        return False

    def __str__(self):
        return f"{self.courier} - from {self.start} to {self.end}"

    def clean(self):
        diff = self.start - self.end
        if diff.total_seconds() == (45 * 60):
            raise ValidationError("Shift window should be at least 45 minutes.")
        elif self.start > self.end:
            raise ValidationError("End time must come after start time.")
        elif self.start.date() != self.end.date():
            raise ValidationError("Shift must be within the same day.")

    def save(self, *args, **kwargs) -> None:

        return super().save(*args, **kwargs)

    # -------------------------------
    def end_pause(self) -> "Courier":
        utc_now = datetime.utcnow()
        utc_now = utc_now.replace(tzinfo=pytz.utc)
        self.courier.paused_at = None
        if self.is_active:
            self.courier.status = Courier.Status.online
        else:
            self.courier.status = Courier.Status.offline
        self.courier.save(update_fields=("status", "paused_at"))
        return self

    def cancel_shift(self):
        if self.status != DashStatus.cancelled:
            self._cancel_dash() if self.is_dash else self._cancel_scheduled()

    def _cancel_dash(self, local_now=None):
        """NOTE:: Apply of DASH shift cancellation policy"""
        with transaction.atomic():
            self.status = DashStatus.cancelled
            self.save(update_fields=("status",))
            count = self.courier.cached.shifts.filter(
                is_dash=True, date__gte=self.date + timedelta(days=15)
            ).count()
            tranz, _created = Transaction.objects.get_or_create(
                wallet_type=WalletType.courier,
                # wallet_id =
                # shift=self,
                type=DebitType.penalty,
            )
            # TODO:: Courier Shift Log , with associated otptonal transaction if cancelled
            _amount = 0 if count < 3 else 1500
            if not _created or _amount == 0:
                return
            tranz.amount = _amount
            tranz.currency = Currency.cdf
            tranz.description = f"dash shift cancellation"
            tranz.save(update_fields=("amount", "currency", "description"))

    def _cancel_scheduled(self):
        """NOTE:: Apply of SCHEDULED shift cancellation policy"""
        # INFO:: Cancelled in less than 12 hours before the shift start
        # first cancellation in the last 15 days cost nothing
        # the 3 following cancellation 2, 3 and 4 will cost 0.25USD
        # from th 5th and more cancelltion in a month 1USD
        tz = pytz.timezone(self.courier.city.timezone)  # e.g. "Africa/Kinshasa"
        local_now = timezone.now().astimezone(tz)
        time_to_start = self.start_at - local_now
        count = self.courier.cached.shifts.filter(
            is_dash=True,
            date__gte=self.date + timedelta(days=15),
        ).count()
        if time_to_start.total_seconds() <= 12 * 60:
            _amount = 0.0 if count < 1 else 0.25 if count <= 3 else 1
        else:
            _amount = 0 if count < 3 else 0.25
        with transaction.atomic():
            self.status = DashStatus.cancelled
            self.save(update_fields=("status",))
            tranz, _created = self.courier.transactions.get_or_create(
                shift=self,
                type=DebitType.penalty,
            )
            if (not _created) or (_amount == 0):
                return
            tranz.amount = _amount
            tranz.currency = self.courier.city.currency
            tranz.description = f"scheduled shift cancellation"
            tranz.save(update_fields=("amount", "currency", "description"))

    def clean(self) -> None:
        # Check for minimum shift duration

        overlapping = self.courier.cached_shifts.filter(
            Q(is_dash=False) & Q(date=self.date) & Q(start__lt=self.end, end__gt=self.start),
        ).exclude(Q(pk=self.pk) & Q(status=DashStatus.cancelled))
        if overlapping.exists():
            raise exceptions.ValidationError("overlaping with an existing shift.")
        shift_start = datetime.combine(self.date, self.start)
        shift_end = datetime.combine(self.date, self.end)

        if self.is_dash and shift_end - shift_start < timedelta(minutes=15):
            raise ValidationError(_("DASH Shift duration can be at least 15 min."))
        elif self.is_dash == False and shift_end - shift_start < timedelta(hours=1):
            raise ValidationError(_("SCHEDULED Shift duration must be at least 1 hour."))
        return super().clean()
