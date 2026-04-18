from model_utils import FieldTracker
from common.models.service import Service
from core.mixin.file_cleanup import FileCleanupMixin
from core.utils import versioned_upload
from django.utils.text import slugify
from core.managers import ObjectsManager
from django.utils.translation import gettext_lazy as _
import logging
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class Item(FileCleanupMixin, models.Model):

    def upload_image(instance, filename):
        return versioned_upload("catalog/item/images/", instance, filename)

    # Core fields
    # - supplier=None → Platform item (for stores)
    # - supplier=value → Supplier item (for kitchens)
    supplier = models.ForeignKey(
        "merchant.Supplier",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
        related_name="items",
    )
    types = models.ManyToManyField(Service, related_name="items")
    name = models.CharField(max_length=100, db_index=True)
    index = models.PositiveSmallIntegerField(default=0)
    image = models.ImageField(max_length=150, upload_to=upload_image, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    description = models.TextField(blank=True)
    usage = models.CharField(max_length=400, blank=True)
    warning = models.CharField(max_length=300, blank=True)
    nutrition_facts = models.JSONField(default=dict, blank=True, null=True, help_text="100g of serving size")
    ingredients = ArrayField(models.CharField(max_length=80), blank=True, default=list)

    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tracker = FieldTracker(fields=["image"])
    objects = ObjectsManager()

    class Meta:
        ordering = ["-is_active", 'index', "name"]

    @property
    def owner(self):
        return self.supplier.name if self.supplier else "Platform"

    @property
    def is_platform(self):
        return self.supplier_id is None

    @property
    def is_supplier(self):
        return self.supplier_id is not None

    @property
    def type_codes(self):
        """Return a list of type codes as strings"""
        return [str(type) for type in self.types.all()]

    def __str__(self):
        return self.name

    def clean(self) -> None:
        # INFO:: This method is automatically cally from django forms such as in the admin pannel
        # we my need to call it explicitly from a vie before caling the save mathod.

        return super().clean()

    def save(self, *args, **kwargs):
        self.cleanup_files()
        super().save(*args, **kwargs)


"""
nutrition_facts = {
    "calories": 250,
    "protein": "10g",
    "carbs": "30g",
    "fat": "12g",
    "sodium": "200mg",
    "fiber": "5g",
    "sugar": "8g"
}

"""
