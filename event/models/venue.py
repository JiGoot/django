from django.db import models

from common.models.boundary.city import City


# Create your models here.
from django.core.exceptions import ValidationError


class Venue(models.Model):
    name = models.CharField(max_length=200)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="venues")
    city = models.ForeignKey(City, on_delete=models.RESTRICT, null=True, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    landmark = models.CharField(max_length=255, null=True, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    def __str__(self):
        if self.parent:
            return f"{self.name} • ({self.parent.name})"
        return self.name

    @property
    def get_city(self):
        if self.city:
            return self.city
        if self.parent:
            return self.parent.city
        return None

    def clean(self):
        # Ensure top-level venues have location info
        if self.parent is None:
            if not all([self.city, self.lat, self.lng, self.address]):
                raise ValidationError("Parent venues requires: city, lat, lng, and address to be set.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
