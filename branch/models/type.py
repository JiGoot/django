# from django.db import models
# from django.utils.functional import classproperty
# from model_utils import FieldTracker

# from core.managers import ObjectsManager
# from core.mixin.file_cleanup import FileCleanupMixin
# from core.utils import versioned_upload


# class BranchType(FileCleanupMixin, models.Model):
#     def upload_image(instance, filename):
#         return versioned_upload("branch/types/images/", instance, filename)

#     code = models.CharField(max_length=32, unique=True, db_index=True)
#     index = models.PositiveSmallIntegerField(default=0)  # Ordering index
#     description = models.TextField(blank=True)
#     image = models.ImageField(max_length=150, null=True, upload_to=upload_image)
#     # Regulatory flags
#     age_check = models.BooleanField(default=False)
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     tracker = FieldTracker(fields=["image"])
#     objects = ObjectsManager()

#     class Meta:
#         ordering = ["index", "code"]
#         verbose_name = "Type"
#         verbose_name_plural = "Types"

#     def __str__(self):
#         return self.code

#     def save(self, *args, **kwargs):
#         self.cleanup_files()
#         super().save(*args, **kwargs)
