from django.db import models
from django.core.files.storage import default_storage
from model_utils import FieldTracker
import logging

logger = logging.getLogger(__name__)

class FileCleanupMixin(models.Model):
    """
    Abstract mixin to automatically delete old files/images when a field changes.
    Models must:
    - define FILE_FIELDS = ['image', 'logo', ...]
    - define FieldTracker per file field at class level
    """
    class Meta:
        abstract = True

    def cleanup_files(self):
        tracker = getattr(self, "tracker", None)
        if not tracker:
            return

        for field_name in tracker.fields:
            field = self._meta.get_field(field_name)
            if not isinstance(field, (models.FileField, models.ImageField)):
                continue

            if tracker.has_changed(field_name):
                old_file = tracker.previous(field_name)
                if old_file and getattr(old_file, "name", None):
                    try:
                        default_storage.delete(old_file.name)
                        logger.debug(f"Deleted old file for {self.__class__.__name__}.{field_name}")
                    except Exception as e:
                        logger.exception(f"Failed to delete old file for field {field_name}: {e}")

            # TODO: ensure current file is in correct path / format if needed

