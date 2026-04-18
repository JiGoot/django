
from django.db import models
from common.models.gateway import Gateway
from core.managers import ObjectsManager
from core.utils import Currency

from django.core.validators import MinValueValidator
from django.db.models import Q, UniqueConstraint
from django.core.exceptions import ValidationError

from customer.models.customer import Customer

class Payment(models.Model):
    class Methods:
        cash = 'cash'
        mpesa = 'm-psea'
        airtel_money = 'airtel-money'
        # orange_money = 'orange-money'
        wallet = 'wallet'

    class Status:
        pending = 'pending'
        paid = 'paid'

    # NOTE:: Choices
    METHODS = (
        (Methods.cash, 'Cash'),  # For On delivery payment
        (Methods.mpesa, 'M-Pesa'),
        (Methods.airtel_money, 'Airtel-Money'),
        # (Methods.orange_money, 'Orange-Money'),
        (Methods.wallet, 'Wallet'),
    )

    # NOTE:: Fields
    customer = models.ForeignKey(Customer, on_delete=models.RESTRICT, related_name='payments')
      # TODO:: Remove null=True
    method = models.CharField(max_length=50, choices=METHODS, default=Methods.cash)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, choices=Currency.choices)
    gateway = models.ForeignKey(Gateway, on_delete=models.SET_NULL, null=True)
    reference = models.CharField(max_length=100, null=True, help_text='Transaction ID')
    created_at = models.DateTimeField(auto_now_add=True)

    # Reference to the service paid by the customer (only one should be non-null)
    # TaxiRide, Subscription, 
    order = models.ForeignKey('order.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    parcel = models.ForeignKey('parcel.Parcel', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    # event = models.ForeignKey('event.EventOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')

    objects = ObjectsManager()

    class Meta:
        constraints = [
            # Enforce that one and only one of the two foreign keys is set
            # reference must be unique if set
            UniqueConstraint(
                fields=['reference'],
                condition=~Q(reference__isnull=True),
                name='unique_non_null_reference'
            )
        ]

    def clean(self):
        if sum(bool(x) for x in [self.order_id, self.parcel_id, self.event_ticket_id]) != 1:
            raise ValidationError("Exactly one of order, parcel, or event_ticket must be set.")


    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
