from branch.models.branch import Branch
from django.db import models
import logging
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from core.utils import Weekday

logger = logging.getLogger(__name__)

from django.db import models
from django.contrib.postgres.fields import ArrayField
from core.utils import Weekday
from django.core.exceptions import ValidationError
from django.contrib.postgres.indexes import GinIndex

class Shift(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="shifts")
    weekdays = ArrayField(
        models.IntegerField(choices=Weekday.choices),
        help_text="Select multiple weekdays for this shift",
    )
    start = models.TimeField(help_text="Local Time")
    end = models.TimeField(help_text="Local Time")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("branch", "weekdays")
        constraints = [
            #  Basic validation: start_time must be before end_time
            models.CheckConstraint(
                condition=models.Q(start__lt=models.F("end")),
                name="start_before_end",
            ),
        ]
        indexes = [
            # Django automatically indexes FK
            GinIndex(fields=["weekdays"]),
            models.Index(fields=["weekdays", "start", "end"]),
        ]

    def __str__(self):
        days = ", ".join(str(Weekday.maps[d]) for d in self.weekdays)
        return f"[{days}] {self.start}-{self.end}"

    def clean(self):
        """Validate the shift data"""
        if not self.weekdays:
            raise ValidationError("At least one weekday must be selected")

        if self.start >= self.end:
            raise ValidationError("End time must be after start time")

        # Remove duplicates and sort
        if self.weekdays:
            self.weekdays = sorted(set(self.weekdays))

    def save(self, *args, **kwargs):
        super().save(*args, kwargs)
