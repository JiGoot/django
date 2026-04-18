from datetime import datetime
from decimal import Decimal
import uuid
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.db import models
from core.utils import Currency, DebitType, TranzMethods, WalletType
from user.models import User


'''
The merchant sees one balance for everything they earn — whether it's:
- From consigned store items
- Or from their kitchens via food businesses
'''
# Create your models here.


class Wallet(models.Model):
    type = models.CharField(max_length=12, choices=WalletType.choices)
    # TODO:: User can have more that one wallet based on the currency first
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE, related_name='wallet')
    # store = models.OneToOneField('store.Store', null=True, blank=True, on_delete=models.CASCADE, related_name='wallet')
    # merchant = models.OneToOneField('merchant.Merchant', null=True, blank=True,
    #                                 on_delete=models.CASCADE, related_name='wallet')
    # courier = models.OneToOneField('courier.Courier', null=True, blank=True,
                                #    on_delete=models.CASCADE, related_name='wallet')
    # TODO:: could add also customer in the future

    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=Currency.choices)
    created_at = models.DateTimeField(auto_now_add=True)



    def internal_reference(self):
        """
        Generate a unique internal reference for a transaction.
        Format: INT-{CONTEXT}-{TYPE}-{DATE}-{SHORTID}
        """

        # Infer context label
        if self.store_id:
            context = "ST"
        elif self.merchant_id:
            context = "MR"
        elif self.courier_id:
            context = "CO"
        else:
            raise ValueError("Transaction missing context")

        tx_type = "CR" if self.type == "credit" else "DB"
        date = datetime.now().strftime('%Y%m%d.%H%M')
        suffix = str(uuid.uuid4())[:6].upper()  # short unique ID
        return f"{context}-{tx_type}{date}.{suffix}"

    def credit(self, amount: Decimal, type: str, order=None, ref=None):
        with db_transaction.atomic():
            self.balance += amount
            self.save(update_fields=('balance',))
            return self.transactions.create(
                type=type,
                amount=+ abs(amount),
                balance=self.balance,
                reference=ref if ref else self.internal_reference(),
                store_id=order.store_id if order else None,
                kitchen_id=order.kitchen_id if order else None,
                courier_id=order.courier_id if order else None,
                order=order,
            )

    def debit(self, amount: Decimal, type: str, order=None, ref=None):
        with db_transaction.atomic():
            self.balance -= amount
            self.save(update_fields=('balance',))
            return self.transactions.create(
                type=type,
                amount=- abs(amount),
                balance=self.balance,
                reference=ref if ref else self.internal_reference(),
                store_id=order.store_id if order else None,
                kitchen_id=order.kitchen_id if order else None,
                courier_id=order.courier_id if order else None,
                order=order,
            )

    # def cod_deposit_tranz(self, order):
    #     # A COD deposit requires that a prior COD collect transaction
    #     tranz = self.transactions.filter(order=order, type=TranzTypes.cod_collect).first()
    #     if not tranz:
    #         raise ValidationError("Correspondint COD Collection transaction not fond")
    #     earning = order.delivery_fee - (order.delivery_fee * Decimal(self.courier.commission_rate))
    #     amount = order.total - earning
    #     if (tranz.amount != amount):
    #         raise ValidationError(
    #             "COD Deposit amount do not match corresponding COD collected transaction amount")
    #     # > Credit only the amount the courier must return to the platform, from the previous COD collect
    #     # This has the effect to cancel the COD collect debit transaction
    #     self._credit(amount, type=TranzTypes.cod_deposit, order=order)
    #     # > For tracking the courier earnings we can create a historical transaction without affecting the
    #     # current wallet's balance
    #     self.transactions.create(
    #         order=order,
    #         type=TranzTypes.delivery_payment,
    #         amount=order.delivery_fee,
    #         balance=self.balance,
    #     )

    def payout(self, staff: User, method: str, amount: Decimal,  currency: str, ref=None):
        '''
        Process a payout for the courier.
        Args:
            staff (User): The staff member initiating the payout.
            method (str): The transaction method (e.g., cash, bank transfer).
            amount (Decimal): The payout amount.
            currency (str): The currency for the payout.

        Raises:
            ValidationError: If the amount is invalid or the courier balance is insufficient.
        '''
        if amount <= 0:
            raise ValidationError("the requested amount must be positive")
        country = self.courier.city.country
        # Validate cash transaction constraints
        if method == TranzMethods.cash:
            country.smallest_bill_check(amount)
        # Retrieve transaction fee and method
        tranz_fee, tranz_method = country.tranz_fee(method, amount, currency)
        # Calculate commission and total required balance
        commission = amount * Decimal(self.courier.commission_rate)
        total = amount + commission
        # Check for sufficient balance
        if self.balance < total:
            raise ValidationError("Insufficient balance to cover payout and commission")
        # Perform the transaction atomically
        _tranzs = []
        with db_transaction.atomic():
            _tranzs.append(self.debit(amount, type=DebitType.payout, ref=ref))

            payout = self.payouts.create(
                staff=staff,
                method=tranz_method,
                amount=amount,
                currency=self.currency
            )
            payout.transactions.set(_tranzs)
