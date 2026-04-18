from django.db import models
from event.models.schedule import EventSchedule

from event.utils import TicketUtils



class TicketTier(models.Model):
    schedule = models.ForeignKey(EventSchedule, on_delete=models.CASCADE)
    name = models.CharField(max_length=20, choices=TicketUtils.Tier.choices)
    location = models.CharField(max_length=20, choices=TicketUtils.Tier.Location.choices, blank=True, null=True)
    section = models.CharField(max_length=1, choices=TicketUtils.Tier.SectionCode.choices, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    extras = models.JSONField(blank=True, null=True)
    capacity = models.PositiveIntegerField()
    sold = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-price"]

    @property
    def available(self):
        # tickets remaining for sale = capacity - sold - unallocated?
        return self.capacity - self.sold

    def __str__(self):
        parts = [self.name]
        if self.location:
            parts.append(f"({self.location})")
        if self.section:
            parts.append(f"Section {self.section.upper()}")
        return " - ".join(parts)