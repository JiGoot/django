import os
import time
from django.db import models
from model_utils import FieldTracker
from common.models.boundary.city import City
from core.managers import ObjectsManager
from core.mixin.file_cleanup import FileCleanupMixin
from core.utils import versioned_upload
from event.models.venue import Venue
from django.core.exceptions import ValidationError
from event.utils import EventUtils
import uuid
from django.contrib.postgres.fields import ArrayField
from merchant.models.merchant import Merchant


class Event(FileCleanupMixin, models.Model):
    def upload_image(instance, filename):
        return versioned_upload("event/images/", instance, filename)
    
    merchant = models.ForeignKey(Merchant, on_delete=models.RESTRICT, related_name="events")
    city = models.ForeignKey(City, on_delete=models.RESTRICT)
    venue = models.ForeignKey(Venue, on_delete=models.RESTRICT)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=EventUtils.Category.choices)
    tags = ArrayField(models.CharField(max_length=50, choices=EventUtils.Tag.choices), blank=True, default=list)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=EventUtils.Status.choices, default=EventUtils.Status.draft)
    image = models.ImageField(upload_to=upload_image, blank=True, null=True)

    min_age = models.PositiveSmallIntegerField(choices=EventUtils.Age.choices, null=True)
    warning = models.CharField(max_length=255, null=True, blank=True)
    # Terms and conditions the customer must accept before purchasing tickets
    # Purchasing is considered acceptance of these terms
    terms = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tracker = FieldTracker(fields=["image"])
    objects = ObjectsManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.merchant.name}, {self.city})"

    def clean(self):
        # Enforce city consistency
        venue_city = self.venue.city or (self.venue.parent.city if self.venue.parent else None)
        if venue_city and self.city != venue_city:
            raise ValidationError("Event city must match the venue (or parent venue) city.")

        # Enforce merchant approval
        if not self.merchant.is_approved:
            raise ValidationError("Event owner must be an approved merchant.")

    def save(self, *args, **kwargs):
        self.full_clean()
        self.cleanup_files()
        super().save(*args, **kwargs)
