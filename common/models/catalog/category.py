import os
import time
import uuid

from model_utils import FieldTracker
from core.mixin.file_cleanup import FileCleanupMixin

from core.utils import versioned_upload
from django.utils.text import slugify
from core.managers import ObjectsManager
from django.utils.translation import gettext_lazy as _
import logging
from django.db import models

from core.managers import ObjectsManager
from django.core.exceptions import ValidationError


logger = logging.getLogger(__name__)


# TODO:: Ensure that a category with parent cannot become itsel a parent, this fixe the level to 2
# That's a crucial constraint to prevent circular references and infinite hierarchies.
class Category(FileCleanupMixin, models.Model):

    def upload_image(instance, filename):
        return versioned_upload("catalog/category/images/", instance, filename)

    # Ownership
    supplier = models.ForeignKey(
        "merchant.Supplier",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="categories",
        help_text="NULL means platform category (stores), NOT NULL means supplier-specific (kitchens)",
    )
    type = models.ForeignKey("common.Service", on_delete=models.RESTRICT, null=True)
    name = models.CharField(max_length=100)
    index = models.PositiveSmallIntegerField(default=0)
    # Hierarchy (used only for store categories)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="subcategories"
    )

    # Ratio 3:4 (512px, ~682px)
    image = models.ImageField(upload_to=upload_image, null=True, blank=True)

    is_active = models.BooleanField(default=False)
    # Tracker for image field
    tracker = FieldTracker(fields=["image"])
    objects = ObjectsManager()

    class Meta:
        ordering = [
            "supplier__name",
            "-is_active",
            "parent__name",
            "name",
        ]
        unique_together = [["name", "parent", "supplier"]]
        constraints = [
            # Platform categories can have hierarchy, supplier categories must be flat
            # models.CheckConstraint(
            #     condition=models.Q(
            #         (models.Q(supplier__isnull=True))  # Platform: can have parent
            #         | (
            #             models.Q(supplier__isnull=False) & models.Q(parent__isnull=True)
            #         )  # Supplier: must be flat
            #     ),
            #     name="valid_category_hierarchy",
            # ),
        ]

        # Optional: Ensure unique names within the same context # Unique per supplier (null for platform)
        # unique_together = [["name", "supplier"]]

    @property
    def is_parent(self):  # If not parent_id, category is parent
        return False if self.parent_id else True

    @property
    def is_subcategory(self):
        return True if self.parent_id else False

    @property
    def owner(self):
        return self.supplier.name if self.supplier else "Platform"

    def __str__(self):
        if self.parent:
            return f"{self.owner} :: {self.parent.name} / {self.name}"
        return f"{self.owner} :: {self.name}"

    def clean(self) -> None:
        # Prevent subcategories (categories with a parent) from being parents of others
        if self.parent and self.parent.is_subcategory:
            raise ValidationError("Subcategories cannot be a parent.")
        # if not self.is_parent and not self.image:
        #     raise ValidationError("Parent categories must have an image.")
        return super().clean()

    def save(self, *args, **kwargs):
        self.clean()  # Ensure clean is called before saving
        self.cleanup_files()
        super().save(*args, **kwargs)
