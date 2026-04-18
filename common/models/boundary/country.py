from django.utils.translation import gettext_lazy as _
from core.utils import CountryCode, Currency
from django.db import models
import logging
from decimal import Decimal
from django.core.exceptions import ValidationError
from core.managers import ObjectsManager

logger = logging.getLogger(__name__)


class Country(models.Model):
    code = models.CharField(
        max_length=2, unique=True, choices=CountryCode.choices,
        help_text="lowerecase ISO 3166-1 alpha-2 country code"
    )
    dial_code = models.CharField(max_length=3, unique=True)
    smallest_bill = models.PositiveSmallIntegerField()
    currency = models.CharField(
        max_length=3, choices=Currency.choices,
        help_text="ISO 4217 currency code"
    )
    objects = ObjectsManager()

    class Meta:
        verbose_name_plural = 'Countries'

    def __str__(self) -> str:
        return self.code

    def smallest_bill_check(self, amount: Decimal):
        """Check if the amount complies with the smallest bill constraint for cash transactions.
        Raise a ValidationError if it does not."""
        if amount % self.smallest_bill != 0:
            raise ValidationError(
                f"The amount must be a multiple of the smallest bill ({self.smallest_bill})."
            )
