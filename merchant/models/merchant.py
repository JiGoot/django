import logging
from django.utils.translation import gettext_lazy as _
from django.db import models
from core.managers import ObjectsManager
from user.models import User
from typing import Optional

logger = logging.getLogger(__name__)


class Merchant(models.Model):
    user = models.OneToOneField(User, on_delete=models.RESTRICT)
    business = models.CharField(max_length=100, unique=True, help_text="Legal name")
    role = models.CharField(max_length=50, null=True)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    objects = ObjectsManager()

    @property
    def name(self):
        return self.user.name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def email(self):
        return self.user.email

    @property
    def tel(self) -> Optional[str]:
        return self.user.tel

    def __str__(self) -> str:
        return str(self.user)


