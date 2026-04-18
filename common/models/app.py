from django.db import models
from common.cached.app import CachedApp
from core.utils import AppOs, ReleaseChannels, ReleaseStages, AppType


# --- 1. The Parent Model: Defines the Application Instance ---
class App(models.Model):
    """
    Represents a specific application on a specific operating system.
    This holds information that is constant across all versions of that combination.
    """

    type = models.CharField(max_length=20, choices=AppType.choices)
    os = models.CharField(max_length=10, choices=AppOs.choices)
    # Platform-Specific Identifier
    # (Android: applicationId / iOS: Bundle Identifier) (e.g., com.jigoot.wwww)
    bundle_id = models.CharField(max_length=100)
    url = models.URLField()

    class Meta:
        unique_together = ("type", "os", "bundle_id")

    # NOTE:: Initialize caching utility
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cached = CachedApp(self)

    def __str__(self):
        return f"{self.type} ➤ {self.os}"


from multiselectfield import MultiSelectField
from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator
from user.models import User
from django.core.exceptions import ValidationError
from packaging import version

# The regex matches:
# ^: Start of the string
# \d+: One or more digits (for major version)
# (\.\d+)*: Zero or more occurrences of (. followed by one or more digits) (for minor/patch versions)
# (\+\d+)?$: Optional group: (\+ followed by one or more digits), anchored to the end of the string
VERSION_REGEX = r"^\d+(\.\d+)*(\+\d+)?$"

version_validator = RegexValidator(
    regex=VERSION_REGEX,
    message="Version must be in the format 'X.Y.Z' or 'X.Y.Z+build_number'.",
    code="invalid_version_format",
)


class Release(models.Model):
    """
    Patch: Backward-compatible bug fixes or internal improvements berly noticed by users.
    """

    app = models.ForeignKey(App, on_delete=models.RESTRICT, related_name="releases")
    version = models.CharField(max_length=20, validators=[version_validator])
    stage = models.CharField(
        max_length=10, choices=ReleaseStages.choices, default=ReleaseStages.dev
    )
    channels = MultiSelectField(
        choices=ReleaseChannels.choices,
        max_choices=6,
        max_length=150,
        default=ReleaseChannels.shorebird,
    )
    min_version = models.CharField(max_length=20, blank=True, null=True)
    changelog = models.TextField(blank=True, null=True)
    # Metadata
    staff = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="releases"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]  # latest version first
        unique_together = ("app", "version")

    def __str__(self):
        return f"v{self.version}"

    def clean(self):
        if self.min_version and version.parse(self.version) < version.parse(
            self.min_version
        ):
            raise ValidationError("Version must be greater than base version.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
