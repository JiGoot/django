from django.utils.translation import gettext_lazy as _
import logging
from django.db import models


logger = logging.getLogger(__name__)


class Variant(models.Model):
    item = models.ForeignKey(
        'common.Item',
        on_delete=models.CASCADE,
        null=True,
        db_index=True,
        related_name="variants",
    )
    index = models.PositiveSmallIntegerField(default=0)
    # The variant otion or item portion
    name = models.CharField(max_length=25, db_index=True)
    weight = models.PositiveIntegerField(help_text="Grams")
    volume = models.PositiveIntegerField(help_text="cm3")
    # For substitution variants
    alternatives = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
    )

    # Platform-level activation
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        unique_together = ["item", "name"]
        ordering = ["item", "index"]

    def __str__(self):
        return f"{self.item.name} - {self.name}"


# def get_alternatives(variant, exclude_variant=None):
#     qs = Variant.alternatives.all(
#         Q(left_alts__right=variant) |
#         Q(right_alts__left=variant)
#     ).exclude(id=variant.id)

#     if exclude_variant:
#         qs = qs.exclude(id=exclude_variant.id)

#     return qs

# qs = qs.annotate(
#     price_delta=Abs(F("price") - source_variant.price)
# ).order_by("price_delta")
