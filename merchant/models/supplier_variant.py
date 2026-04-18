from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import logging
from django.utils.translation import gettext_lazy as _
from django.db import models
from model_utils import FieldTracker
from common.models.catalog.category import Category
from common.models.catalog.variant import Variant
from core.managers import ObjectsManager
from merchant.models.supplier import Supplier

logger = logging.getLogger(__name__)


class SupplierVariant(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.RESTRICT, related_name="supplier_variants")
    category = models.ForeignKey(Category, on_delete=models.RESTRICT, related_name="supplier_variants")
    # Base line discount
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(
        default=0, max_digits=5, decimal_places=4, validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = ObjectsManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["supplier", "category", "variant"], name="unique_variant_per_supplier_per_category"
            )
        ]

    @property
    def name(self):
        return f"{self.variant.item.name} - {self.variant.name}"

    def __str__(self):
        return self.name

    def clean(self):
        if not self.category.parent:
            raise ValidationError("variant can only belong to a subcategory")