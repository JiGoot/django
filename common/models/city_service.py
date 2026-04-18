from django.db import models
from common.models.boundary.city import City
from common.models.service import Service
from core.managers import ObjectsManager


class CityService(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    min_age = models.PositiveSmallIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = ObjectsManager()

    class Meta:
        ordering = ["service__index"]
        unique_together = ("city", "service")

    def __str__(self):
        return f"{self.city.name} - {self.service.name}"

    def clean(self):
        # Logic: If the Service requires an age check, the CityService must define the age.
        if self.service.age_check and self.min_age is None:
            raise ValueError({"min_age": f"The {self.service.name} service requires a minimum age to be set."})

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensures validation runs even outside of Admin
        super().save(*args, **kwargs)
