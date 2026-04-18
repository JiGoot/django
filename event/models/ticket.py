from django.db import models
from event.models.schedule import EventSchedule
from event.models.ticket_order import TicketOrder
from django.core.exceptions import ValidationError
from event.models.ticket_tier import TicketTier
from event.utils import TicketUtils


class Ticket(models.Model):
    order = models.ForeignKey(TicketOrder, on_delete=models.CASCADE, related_name="tickets")
    tier = models.ForeignKey(TicketTier, on_delete=models.RESTRICT, related_name="tickets")
    schedule = models.ForeignKey(EventSchedule, on_delete=models.RESTRICT)
    # qty is usually 1-per-ticket; can bulk split internally
    qty = models.PositiveIntegerField(default=1)
    # snapshot of the ticket price at the time of purchase
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=TicketUtils.Status.choices, default=TicketUtils.Status.active
    )
    # optional, when seating is implemented
    seat = models.CharField(max_length=50, null=True, blank=True)
    # e.g. "A-12", "VIP-03", "BALCONY_B_7"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            # No seat is sold twice for a schedule
            models.UniqueConstraint(fields=["schedule", "seat"], name="unique_ticket_per_seat_schedule"),
        ]

    def __str__(self):
        if self.seat:
            return f"{self.tier} - Seat: {self.seat} - {self.qty} - {self.status}"
        return f"{self.tier} - {self.qty} - {self.status}"

    def clean(self):
        if self.order.schedule_id != self.schedule_id:
            raise ValidationError("Order schedule mismatch.")
        if self.tier.schedule_id != self.schedule_id:
            raise ValidationError("Tier schedule mismatch.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
