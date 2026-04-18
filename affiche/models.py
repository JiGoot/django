import logging
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from model_utils import FieldTracker
from core.managers import ObjectsManager
from core.mixin.file_cleanup import FileCleanupMixin
from core.utils import versioned_upload


logger = logging.getLogger(__name__)
# Create your models here.


class Affiche(FileCleanupMixin, models.Model):
    IMAGE_PATH = "affiche/images/"

    def upload_image(instance, filename):
        return versioned_upload("affiche/images/", instance, filename)

    city = models.ForeignKey("common.City", on_delete=models.CASCADE, related_name="affiches")
    name = models.CharField(max_length=100, unique=True, help_text="Campagn name")
    # size=(854, 356),  # 480p , 2.4:1
    image = models.ImageField(upload_to=upload_image)
    index = models.PositiveSmallIntegerField(default=0)
    start = models.DateField(null=True, blank=True)
    end = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    tracker = FieldTracker(fields=["image"])
    objects = ObjectsManager()

    class Meta:
        ordering = ["city", "index"]
        unique_together = (("city", "name"),)

    def __str__(self):
        return self.name

    def clean(self) -> None:
        if (self.start and not self.end) or (not self.start and self.end):
            raise ValidationError("Start and end should both be null or not null")
        if self.start:
            if self.start < timezone.now():
                raise ValidationError("Campagne start cannot be in the past.")
        return super().clean()

    def save(self, *args, **kwargs):
        self.cleanup_files()
        super().save(*args, **kwargs)
