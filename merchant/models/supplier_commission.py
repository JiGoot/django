from django.db import models
from core.managers import ObjectsManager
from core.utils import CommissionType


"""
On creation update `supplier.commision
When commission changes:
    1. Close previous record:
        valid_to = now()

    2. Create new record:
        valid_from = now()
        valid_to = null
"""


class SupplierCommission(models.Model):
    supplier = models.ForeignKey("merchant.Supplier", on_delete=models.CASCADE, related_name="commissions")
    type = models.CharField(max_length=50, choices=CommissionType.choices)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    start = models.DateTimeField(auto_now_add=True)   # auto-filled
    end = models.DateTimeField(null=True, blank=True)
    objects = ObjectsManager()

