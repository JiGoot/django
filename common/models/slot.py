import logging
from core.managers import ObjectsManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class Slot(models.Model):
    """
    Slot Model

    Represents a time window in the platform that serves dual purposes:
    1. Courier shifts: Couriers select one or more slots when defining their working shifts.
    2. Customer delivery scheduling: Customers can pick delivery windows from slots with available courier coverage.

    Fields:
        - `start` (TimeField): Start time of the slot (e.g., 08:00).
        - `end` (TimeField): End time of the slot (e.g., 08:45).
        - `max_capacity` (PositiveSmallIntegerField): Maximum number of couriers that can register for this slot.
            Used for capacity management and peak/off-peak handling.

    Design Principles and Requirements:
        - Uniform Slot Duration: All slots are of the same length (e.g., 30–45 min) for simplicity and flexibility.
        - `City`/`Zone` Independence: Slots are reusable across all cities/zones; availability is determined by registered courier shifts.
        - Capacity Management: `max_capacity` controls peak vs off-peak usage, preventing overbooking.
        - Shift Tracking: The system can count the number of registered shifts per slot per date.
        - Customer Scheduling: Only slots with at least one registered courier shift for a date are selectable for delivery.
        - Simplicity and Scalability: Single table reused across zones and days; easy to maintain and query.
        - Analytics Ready: Annotate shifts per slot per date for reporting or dashboards.

    Usage Examples:
        # 1. Count registered courier shifts per slot for a given date
        ```python
        from django.db.models import Count, Q
        from datetime import date

        target_date = date.today()
        slots_with_shift_counts = Slot.objects.annotate(
            total_shifts=Count(
                "couriershift",
                filter=Q(couriershift__start_at__date=target_date)
            )
        )
        for slot in slots_with_shift_counts:
            print(slot.start, slot.end, slot.total_shifts)
        ```

        # 2. Filter available slots for customer scheduling
        ```
        available_slots = [
            slot for slot in slots_with_shift_counts
            if slot.total_shifts < slot.max_capacity
        ]
        ```

        # 3. Assigning slots to a courier shift
        Couriers select one or more slots; system materializes shift `start_at` and `end_at` from selected slots.

    Notes:
        - Supports both scheduled and ASAP deliveries (ASAP ignores slots and assigns any active courier).
        - Keeps the system simple, flexible, and scalable for long-term use.
    """

    start = models.TimeField()
    end = models.TimeField()
    # INFO:: This is not the max capacity of a delivery slot, some time such value can be exceeded
    max_capacity = models.PositiveSmallIntegerField(default=10)
    objects = ObjectsManager()

    def __str__(self):
        def _format(v):
            return "%02d:%02d" % (v.hour, v.minute)

        return f"{_format(self.start)} - {_format(self.end)}"

    @property
    def curr_capacity(self) -> int:
        """Get current capacity"""
        pass

    def clean(self) -> None:
        # Check for minimum shift duration
        if self.start == self.end:
            raise ValidationError("Start and end time cannot be equal.")
        elif self.start > self.end:
            raise ValidationError("End time must come after start time.")
        return super().clean()

    class Meta:
        ordering = ["start"]
        unique_together = [("start", "end")]
