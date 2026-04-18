from django.db import models
from decimal import Decimal
from core.managers import ObjectsManager
from core.utils import Currency


class BaseWallet(models.Model):
    '''Abstract'''
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    currency = models.CharField(max_length=3, choices=Currency.choices)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = ObjectsManager()

    class Meta:
        abstract = True

    def credit(self, amount: Decimal, type:str, order=None):
        raise NotImplementedError()

    def debit(self, amount: Decimal, type:str, order=None):
        raise NotImplementedError()
