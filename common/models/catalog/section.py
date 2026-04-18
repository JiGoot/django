from django.utils.translation import gettext_lazy as _
import logging
from django.db import models

from common.models.catalog.category import Category


logger = logging.getLogger(__name__)


class Section(models.Model):
    name = models.CharField(max_length=100, unique=True)
    index = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_active", "index", "name"]

    def __str__(self):
        return self.name


class SectionCategory(models.Model):
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="section_categories"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="section_categories"
    )
    index = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ("section", "category")
        ordering = ["-is_active", "index"]
