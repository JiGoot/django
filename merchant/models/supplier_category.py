# from django.core.validators import MinValueValidator, MaxValueValidator
# from django.core.exceptions import ValidationError
# import logging
# from django.utils.translation import gettext_lazy as _
# from django.db import models
# from common.models.catalog.category import Category
# from common.models.branch_type import BranchType
# from merchant.models.supplier import Supplier

# logger = logging.getLogger(__name__)


# class SupplierCategory(models.Model):
#     branch_type = models.ForeignKey(BranchType, on_delete=models.RESTRICT)
#     supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
#     category = models.ForeignKey(Category, on_delete=models.RESTRICT)
#     name = models.CharField(max_length=150, null=True, blank=True, help_text="Custom name")
#     index = models.PositiveSmallIntegerField()
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         constraints = [
#             models.UniqueConstraint(
#                 fields=["branch_type", "supplier", "category"],
#                 name="unique_category_per_type_supplier",
#             )
#         ]
