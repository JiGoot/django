from model_utils import FieldTracker
from core.mixin.file_cleanup import FileCleanupMixin
from core.utils import DialCode, versioned_upload
import logging
from django.core.exceptions import ValidationError
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from core.utils import Gender, DialCode
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Optional

"""
when I run createsuperuser this is the order in which i will fill information
USERNAME_FIELD -> REQUIRED_FIELDS -> password -> password (again)
NOTE that [password], [first_name], [last_name], [email] and more are inherited from the [AbstractUser] class
"""


from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)

from django.contrib.auth.base_user import BaseUserManager


class _UserCreationManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Hash the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(FileCleanupMixin, AbstractBaseUser, PermissionsMixin):
    def upload_image(instance, filename):
        return versioned_upload("user/profile/images/", instance, filename)

    name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices)
    birthday = models.DateField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    dial_code = models.CharField(max_length=3, choices=DialCode.choices)
    phone = models.CharField(max_length=10)
    password = models.CharField(_("password"), max_length=128, blank=True)
    # size=[512, 512],
    image = models.ImageField(upload_to=upload_image, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    tracker = FieldTracker(fields=["image"])
    objects = _UserCreationManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "last_name"]

    @property
    def tel(self) -> Optional[str]:
        return f"+{self.dial_code}{self.phone}" if self.dial_code and self.phone else None

    @property
    def phone_otp_cache_key(self):
        return f"user-{self.id}::reset_otp_{self.dial_code}{self.phone}"

    @property
    def email_otp_cache_key(self):
        return f"user-{self.id}::reset_otp_{self.email}"

    class Meta:
        ordering = ("name", "last_name")
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(email__isnull=False),
                name="user_unique_email",
                violation_error_message="Email already taken",
            ),
            models.UniqueConstraint(
                fields=["dial_code", "phone"],
                condition=models.Q(dial_code__isnull=False, phone__isnull=False),
                name="user_unique_phone",
                violation_error_message="Phone number already taken!",
            ),
        ]

    def __str__(self):
        return (
            f"{self.name.capitalize()} {self.last_name.capitalize()}"
            if self.last_name
            else self.name.capitalize()
        )

    def clean(self):
        # INFO:: This method is automatically cally from django forms such as in the admin pannel
        # we my need to call it explicitly from a vie before caling the save mathod.
        return super().clean()

    def save(self, *args, **kwargs) -> None:
        if not self.email and not (self.dial_code and self.phone):
            raise ValidationError("Either email or phone number must be provided.")
        self.cleanup_files()
        super().save(*args, **kwargs)
