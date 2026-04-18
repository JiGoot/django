from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class Customer_PSWValidator:
    def __call__(self, password: str):
        if (len(password) < 8):
            raise ValidationError("Password requires at least 8 characters.")
