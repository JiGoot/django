from django.db import models
from event.models.event import Event
from event.models.venue import Venue
from django.core.exceptions import ValidationError


class EventSchedule(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="schedules")
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name="schedules")
    date = models.DateField()
    start = models.TimeField()
    duration = models.DurationField(null=True, blank=True)
    end = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "start"]
        unique_together = ("event", "venue", "date", "start")

    def __str__(self):
        if self.end:
            return f"{self.event.name} on {self.date} from {self.start.strftime('%H:%M')} to {self.end.strftime('%H:%M')}"
        elif self.duration:
            return f"{self.event.name} on {self.date} at {self.start.strftime('%H:%M')} ({self.duration})"
        return f"{self.event.name} on {self.date} at {self.start.strftime('%H:%M')}"

    def clean(self):
        if self.end and self.duration:
            raise ValidationError("Provide either end time or duration, not both.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
