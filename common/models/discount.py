# import logging
# from common.base.wallet import BaseWallet
# from core.utils import CreditType, DebitType
# from django.db import models
# from django.core.validators import MinValueValidator, MaxValueValidator
# from datetime import timedelta
# from kitchen.models.kitchen import FoodBusiness
# from kitchen.models.kitchen.order import KitchenOrder
# from user.models import User
# from django.db import models, transaction
# from core.utils import TranzMethods
# from decimal import Decimal
# from datetime import timedelta 
# from kitchen.apps import SupplierConfig
# from django.utils.translation import gettext_lazy as _
# from django.core.validators import MinValueValidator, MaxValueValidator
# from django.db import models
# from django.db.models import Q
# from django.utils import timezone

# logger = logging.getLogger(__name__)
# '''
# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------
#                     COMMISSION DISCOUNT
# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------
# '''


# class CommissionDiscount(models.Model):
#     """
#     - The Commission discount is active once created (even if `min_sales` isn’t met yet or `start_at` not defined yet).
#     - The commision discount period starts at `start_at`, which can be set on cration or 
#     when `min_sales` is reached.
#     - If `min_sales == 0`, `count_started_at` is set immediately.
#     """
#     kitchen = models.OneToOneField(FoodBusiness, on_delete=models.CASCADE,
#                                    null=True, related_name='commission_discount')
#     commission_rate = models.DecimalField(max_digits=3, decimal_places=2,
#                                           validators=[MinValueValidator(0), MaxValueValidator(0.15)])
#     days = models.PositiveIntegerField(validators=[MaxValueValidator(30)])
#     min_sales = models.PositiveIntegerField(
#         help_text="Minimum sales required before the discount period starts.")
#     sales = models.PositiveIntegerField(default=0, editable=False)
#     start_at = models.DateTimeField(
#         null=True, blank=True, help_text="Set if you want the discount period to start at a predefined data")  # Renamed from `started_at`
#     created_at = models.DateTimeField(default=timezone.now)

#     class Meta:
#         db_table = f'{SupplierConfig.name}_commission_discount'
#         verbose_name = 'Commission discount'
#         verbose_name_plural = 'Commission discounts'
#         ordering = ('created_at',)

#     def is_active(self):
#         now = timezone.now()
#         if not self.start_at:
#             return True  # Discount is active but waiting for `min_sales`
#         return now < (self.start_at + timedelta(days=self.days))

#     def record_sale(self):
#         """Call this method whenever a sale is recorded."""
#         self.sales += 1
#         if self.sales >= self.min_sales and not self.start_at:
#             self.start_at = timezone.now()  # Set start date if min_sales is reached
#         self.save(update_fields=['sales', 'start_at'])


