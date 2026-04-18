from django.db import models
from customer.models.customer import Customer
from event.models.schedule import EventSchedule
from event.models.ticket_tier import TicketTier
from event.utils import TicketUtils


class TicketOrder(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="ticket_orders")
    schedule = models.ForeignKey(EventSchedule , on_delete=models.PROTECT, related_name="orders")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=TicketUtils.OrderStatus.choices, default=TicketUtils.OrderStatus.pending
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def total(self):
        return self.subtotal + self.service_fee

