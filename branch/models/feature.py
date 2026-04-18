import logging
from django.db import models

from branch.models.branch import Branch

logger = logging.getLogger(__name__)


class Feature(models.Model):
    label = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.label


class FeatureBranch(models.Model):
    """
    The amount it costs the platform, to acquire or produce the item
    Or the aggreed share of the merchant(consignor) per consignment item sold
    """

    feature = models.ForeignKey(
        Feature, on_delete=models.CASCADE, related_name="branches"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="features"
    )
    index = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ("feature", "branch")
        ordering = ("index",)
