from common.models.gateway import Gateway
from core.rabbitmq.broker import publisher
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
import re
from django.db.models import Q
from django.db.models import Q, UniqueConstraint
import logging
from common.base.token import AbstractToken
from core.managers import ObjectsManager
from core.utils import SubstitutionPref, formattedError, update_user_timestamp
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from customer.apps import CustomerConfig
from user.models import User

logger = logging.getLogger(__file__)


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.RESTRICT, null=True)
    # TODO Update if customer has already place 5~10 orders
    # supende if cancellation rate is greater than 40~60%
    score = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=100,
        validators=(MinValueValidator(0), MaxValueValidator(100)),
    )
    substitution_pref = models.CharField(
        max_length=20,
        choices=SubstitutionPref.choices,
        default=SubstitutionPref.best_match,
    )
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        ordering = ["user__name", "user__last_name"]

    @property
    def is_authenticated(self):
        return True

    @property
    def gender(self):
        return self.user.gender

    @property
    def dial_code(self):
        return self.user.dial_code

    @property
    def phone(self):
        return self.user.phone

    def __str__(self) -> str:
        return self.user.name

    @staticmethod
    def password_validator(password):
        if len(password) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        if not re.search(r"[A-Za-z]", password):
            raise ValueError("Le mot de passe doit contenir au moins une lettre.")
        if not re.search(r"\d", password):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre.")

    class Tasks:
        @staticmethod
        def update_last_seen(id: int, dt: str):
            update_user_timestamp(Customer, id, dt, "last_seen")


class CustomerDevice(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="device")
    fcm = models.CharField(max_length=255, null=True, unique=True, editable=False)
    # Unique but nullable: Multiple NULLs are allowed, but tokens must be unique
    fcm = models.CharField(max_length=255, null=True, blank=True, unique=True, editable=False)
    # The session identifier (JTI or Token string)
    refresh_token = models.TextField(null=True, blank=True, unique=True, editable=False)
    name = models.CharField(max_length=50, default="unknown", editable=False)
    platform = models.CharField(max_length=20)  # ios, android, web, mac, windows
    last_active = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # db_table = f"{CustomerConfig.name}_device"
        verbose_name = "Device"
        verbose_name_plural = "Devices"
        ordering = ["last_active"]
        indexes = [models.Index(fields=["fcm"])]

    def __str__(self):
        return f"{self.customer} ➤ {self.device}"

    class Tasks:
        @staticmethod
        def update_last_active(id: str, dt: str):
            try:
                device = CustomerDevice.objects.get(id=id)

                timestamp = parse_datetime(dt)
                if timestamp is None:
                    logger.warning(f"Invalid datetime string '{dt}' for CustomerDevice Key")
                    return
                if timestamp.tzinfo is None:
                    timestamp = make_aware(timestamp)

                device.last_active = timestamp
                device.save(update_fields=["last_active"])

            except CustomerDevice.DoesNotExist:
                logger.warning(f"CustomerDevice with id <{id}> does not exist.")
            except Exception as e:
                logger.error(formattedError(e))

    def save(self, *args, **kwargs):
        if not self.pk:
            now = timezone.now()
            publisher.publish(CustomerDevice.Tasks.update_last_active, self.id, now.isoformat())
        return super().save(*args, **kwargs)


"""
---------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------
                    STORE
---------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------
"""

# class CustomerBlackList(models.Model):
#     user = models.OneToOneField(Customer, on_delete=models.CASCADE)
#     date = models.DateTimeField(auto_now_add=True)
#     reason = models.CharField(max_length=250, null=True, blank=False)
#     objects = ObjectsManager()

#     def __str__(self) -> str:

#         return f"{self.user.name}"
