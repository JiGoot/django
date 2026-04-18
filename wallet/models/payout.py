import logging
from django.db import models
from common.models.gateway import Gateway
from core.managers import ObjectsManager
from core.utils import Currency, PayoutStatus
from user.models import User
from wallet.models.wallet import Wallet

logger = logging.getLogger(__name__)

'''
------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------
                    METHOD
------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------
'''


class Payout(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='payouts')
    provider = models.CharField(max_length=50) 
    number = models.CharField(max_length=20)    # Add appropriate max_length
    holder = models.CharField(max_length=100)  # Add appropriate max_length

    staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='payouts')
    status = models.CharField(max_length=10, choices=PayoutStatus.choices,
                              default=PayoutStatus.pending)
    amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    currency = models.CharField(max_length=3, choices=Currency.choices)
    note = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = ObjectsManager()

    class Meta:
        ordering = ['-created_at']
        # indexes = [
        #     models.Index(fields=['wallet_type', 'wallet_id']),
        # ]


'''
------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------
                PAYOUT    METHOD
------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------
'''


class PayoutMethod(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='methods')
    gateway = models.ForeignKey(Gateway, on_delete=models.RESTRICT, null=True)
    number = models.CharField(max_length=16)
    holder = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ObjectsManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['wallet'],
                condition=models.Q(is_default=True),
                name='unique_default_per_wallet'
            )
        ]

    def __str__(self):
        return f"{self.provider} - {self.number}"
