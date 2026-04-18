from datetime import timedelta
from django.db import models
from django.db.models import Case, When, Value, IntegerField
from django.utils.functional import classproperty

from branch.models.branch import Branch


class DeliveryType(models.Model):
    class Codes:
        asap = "asap"
        same_day = "same_day"
        next_day = "next_day"

        @classproperty
        def choices(cls):
            return ((cls.asap, "ASAP"), (cls.same_day, "Same-day"), (cls.next_day, "Next-day"))

        @classproperty
        def values(cls):
            return tuple(v for v, _ in cls.choices)

    class QuerySetManager(models.QuerySet):
        def ordered(self):
            return self.order_by(
                Case(
                    When(code=DeliveryType.Codes.asap, then=Value(1)),
                    When(code=DeliveryType.Codes.same_day, then=Value(2)),
                    When(code=DeliveryType.Codes.next_day, then=Value(3)),
                    output_field=IntegerField(),
                )
            )

    # == FIELDS ==
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="delivery_types")
    code = models.CharField(max_length=20, choices=Codes.choices, null=True)
    # Overwrite the delivery_type Dispatch tuning
    base_dispatch_buffer = models.DurationField(null=True, blank=True)  # minutes
    max_dispatch_buffer = models.DurationField(null=True, blank=True)  # minutes
    extra_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    # Cutoff time for accepting orders of this delivery type, in branch local time.
    # It the latest time of the day that an order can be accepted for this delivery type.
    # For example, if cutoff_time is 18:00, then no orders of this type will be accepted after 18:00,
    # and all orders of this type must be accepted before 18:00. This is useful for same-day delivery types,
    # where the branch needs to stop accepting orders at a certain time to ensure timely delivery.
    # Null means no cutoff, always accept orders of this delivery type
    cutoff_time = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    objects = QuerySetManager.as_manager()

    class Meta:
        unique_together = ("branch", "code")
