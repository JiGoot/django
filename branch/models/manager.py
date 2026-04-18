from typing import Union
from django.core.exceptions import ValidationError
import re
from django.utils import timezone
from model_utils import FieldTracker
from branch.models.branch import Branch
from core.rabbitmq.broker import publisher
from common.base.token import AbstractToken
from core.utils import formattedError, update_user_timestamp
from django.contrib.auth.hashers import make_password, check_password
from core.managers import ObjectsManager
from django.db import models
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import MinLengthValidator, RegexValidator


"""
NOTE:: We went with a single model for branch managers instead of two (StoreManage, KitchenManager), cause we are using one app
for both store and kitchen managment. so with two models it would have been harder to check the token to determin if the token beelong to a kitchen or store.
The two models approach works for separate apps, be which would lead to much redundances."""


class BranchManager(AbstractBaseUser):
    username = models.CharField(
        max_length=100,
        unique=True,
        validators=[
            RegexValidator(
                r"^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+.(duka|kitchen|grocery|cellar|pharmacy|beauty)",
                "Username must be like name@grocery.cd or name@kitchen.ci",
            )
        ],
        help_text="e.g. alain@grocery.cd or marie@kitchen.ci",
    )
    # password = models.CharField(max_length=128)  # hashed
    code = models.CharField(
        max_length=6,
        null=True,
        blank=True,
        validators=[
            MinLengthValidator(3),
            RegexValidator(
                regex=r"^[a-z0-9]+$",
                message="Code must be 3 to 8 lowercase alphanumeric characters.",
            ),
        ],
        help_text="Auto-generated if not set. Admin code: 3 to 8 lowercase alphanumeric characters. Is secret and private",
    )
    last_seen = models.DateTimeField(blank=True, null=True, help_text="API last login")
    branch = models.OneToOneField(
        Branch, null=True, on_delete=models.CASCADE, related_name="manager"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    tracker = FieldTracker(fields=["username"])
    objects = ObjectsManager()
    USERNAME_FIELD = "username"

    class Meta:
        ordering = ("-last_seen", "-created_at")

    @property
    def is_authenticated(self):
        return True

    @property
    def type(self):
        return self.branch.type

    @property
    def is_active(self):
        return self.branch.is_active

    # def set_password(self, raw_pwd: str):
    #     self.validator(raw_pwd)
    #     self.password = make_password(raw_pwd)
    #     self.save(update_fields=['password'])

    @staticmethod
    def password_validator(password):
        if len(password) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        if not re.search(r"[A-Za-z]", password):
            raise ValueError("Le mot de passe doit contenir au moins une lettre.")
        if not re.search(r"\d", password):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre.")

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        # if self.pk is None or self.tracker.has_changed("username"):
        #     country_code = self.branch.city.country_code
        #     if self.branch and not self.username.endswith(f"@branch.{country_code}"):
        #         raise ValidationError(f"Username must end with @branch.{country_code}")

        if self.password and not self.password.startswith("pbkdf2_"):
            self.password_validator(self.password)
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    class Tasks:
        @staticmethod
        def update_last_seen(id: int, dt: str):
            update_user_timestamp(BranchManager, id, dt, "last_seen")

        @staticmethod
        def update_last_login(id: int, dt: str):
            update_user_timestamp(BranchManager, id, dt, "last_seen")


class BranchManagerToken(AbstractToken):
    manager = models.OneToOneField(
        BranchManager,
        related_name="token",
        on_delete=models.CASCADE,
        verbose_name=_("User"),
    )
    device = models.CharField(max_length=50, default="unknown", editable=False)
    fcm = models.CharField(max_length=255, null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    
    class Meta:
        # db_table = f'{StoreConfig.name}_manager_token'
        verbose_name = "Manager Token"
        verbose_name_plural = "Manager Tokens"
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
            now = timezone.now()
            publisher.publish(
                BranchManager.Tasks.update_last_login, self.manager.id, now.isoformat()
            )
        return super().save(*args, **kwargs)
