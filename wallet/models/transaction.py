from django.core.exceptions import ValidationError
import datetime
from django.db import models
from shortuuid import uuid
from common.models.gateway import Gateway
from core.utils import CreditType, Currency, DebitType, WalletType
from wallet.models.wallet import Wallet

'''
The merchant sees one balance for everything they earn — whether it's:
- From consigned store items
- Or from their kitchens via food businesses
'''
# Create your models here.

class Transaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=10, choices=CreditType.choices+DebitType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255, null=True, blank=True)

    # INFO:: typically holds an external or internal identifier that helps trace or uniquely identify the transaction's origin or related operation.
    # ID from a 3rd-party like Stripe, MobileMoney, PayPal, Bank ref (for widrawal) ...
    gateway = models.ForeignKey(Gateway, on_delete=models.SET_NULL, null=True, blank=True)
    reference = models.CharField(max_length=255, null=True, blank=True)
    # TODO:: Add a user as recipient
    # # Optional links to source context
    # store = models.ForeignKey('store.Store', null=True, blank=True, on_delete=models.SET_NULL, related_name='transactions')
    # kitchen = models.ForeignKey('kitchen.Kitchen', null=True, blank=True, on_delete=models.SET_NULL, related_name='transactions')
    # courier = models.ForeignKey('courier.Courier', null=True, blank=True, on_delete=models.SET_NULL, related_name='transactions')
    # Optional link to the order
    order = models.ForeignKey('order.Order', null=True, blank=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # INFO:: Credit must be positive, debit must be negative
            models.CheckConstraint(
                condition=(
                    models.Q(type__in=CreditType.values, amount__gt=0) |
                    models.Q(type__in=DebitType.values, amount__lt=0)
                ),
                name="txn_valid_amount_sign",
            ),

            # INFO:: Amount must not be zero
            models.CheckConstraint(
                condition=~models.Q(amount=0),
                name="txn_amount_non_zero",
            ),
        ]

    @property
    def context(self):
        if self.store_id:
            return self.store
        elif self.kitchen_id:
            return self.kitchen
        elif self.courier_id:
            return self.courier
        elif self.consignment_id:
            return self.consignment
        return None
    
    @property
    def currency(self):
        return self.wallet.currency

    def __str__(self):
        return self.reference

    


    def save(self, *args, **kwargs):
        # Ensure exactly one context is set 
        context_ids = [
            self.store_id,
            self.kitchen_id,
            self.courier_id,
            self.consignment_id,
        ]
        if sum(bool(x) for x in context_ids) != 1:
            raise ValidationError("Transaction must be linked to exactly one context.")

        # Prevent updates to existing records
        if self.pk:
            raise ValueError("Transaction cannot be modified once created.")

        super().save(*args, **kwargs)

