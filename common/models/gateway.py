import logging
from django.db import models
from django.db.models import Q, CheckConstraint, F
from django.utils.translation import gettext_lazy as _

from common.models.boundary.country import Country
from core.utils import Currency

logger = logging.getLogger(__name__)


class Gateway(models.Model):
    '''TODO:: currently for kitchen payout provider, can later turn into payment provider, to include
    both kitchen payout method and customer payment method [PaymentMethod]'''

    PROVIDERS = (
        ('m-pesa', 'M-Pesa'),
        ('airtel-money', 'Airtel Money'),
        ('orange-money', 'Orange Money'),
    )
    country = models.ForeignKey(Country, on_delete=models.RESTRICT)
    currency = models.CharField(max_length=3, null=True,  choices=Currency.choices)
    name = models.CharField(max_length=20, choices=PROVIDERS)
    # INFO:: Min-Max deposit
    min = models.DecimalField(max_digits=10, decimal_places=2)
    max = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['country', 'name']
        unique_together = ('country', 'name', 'currency')


class GatewayRule(models.Model):
    gateway = models.ForeignKey(Gateway, on_delete=models.RESTRICT, related_name='rules')
    min = models.DecimalField(max_digits=10, decimal_places=2)
    max = models.DecimalField(max_digits=10, decimal_places=2)
    fixed_fee = models.DecimalField(max_digits=10, decimal_places=2)
    percent_fee = models.DecimalField(max_digits=4, decimal_places=3)

    @property
    def currency(self):
        return self.gateway.currency

    class Meta:
        ordering = ['gateway', 'min', 'max']
        constraints = [
            CheckConstraint(condition=Q(min__lt=F('max')), name='min_less_than_max'),
        ]

    def __str__(self) -> str:
        return str(self.gateway)


