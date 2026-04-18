from model_utils import FieldTracker
from branch.models.branch import Branch
from common.models.catalog.category import Category
from django.db import models
from django.db.models import Sum, Max
# from django.core.validators import MinValueValidator, MaxValueValidator
# from core.managers import ObjectsManager
# from core.utils import StockMovementType
# from django.utils.translation import gettext_lazy as _
# import logging
# from django.db import transaction

# from merchant.models.supplier_category import SupplierCategory

# logger = logging.getLogger(__name__)


# class BranchCategory(models.Model):
#     """
#     The amount it costs the platform, to acquire or produce the item
#     Or the aggreed share of the merchant(consignor) per consignment item sold
#     """

#     branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="branch_categories")

#     category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="branch_categories")

#     supplier_category = models.ForeignKey(
#         SupplierCategory, on_delete=models.CASCADE, null=True, related_name="supplier_categories"
#     )
#     is_active = models.BooleanField(default=False)
#     # --- Ranking fields (computed via scheduled job) ---
#     popularity_score = models.FloatField(default=0, db_index=True)
#     updated_at = models.DateTimeField(auto_now=True)
