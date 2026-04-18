from django.db import models
from core.utils import versioned_upload
from model_utils import FieldTracker
from core.managers import ObjectsManager
from core.mixin.file_cleanup import FileCleanupMixin

class Service(FileCleanupMixin, models.Model):

    def upload_logo(instance, filename):
        return versioned_upload("service/logos/", instance, filename)

    def upload_image(instance, filename):
        return versioned_upload("service/images/", instance, filename)
    
    index = models.PositiveSmallIntegerField(default=0)
    name = models.CharField(max_length=32, unique=True, db_index=True)
    description = models.TextField(blank=True)
    is_branch_less = models.BooleanField()
    age_check = models.BooleanField(default=False)
    logo = models.ImageField(null=True, blank=True, upload_to=upload_logo)
    image = models.ImageField(null=True, blank=True, upload_to=upload_image)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    tracker = FieldTracker(fields=["logo", "image"])
    objects = ObjectsManager()

    class Meta:
        ordering = ["index", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.cleanup_files()
        super().save(*args, **kwargs) 

    # future: pricing model, SLA rules

