from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class CourierPasswordValidator:
    def __call__(self, password: str):
        if len(password) < 6:
            raise ValidationError(
                _("This password is too short. It must contain at least 6 characters."),
                code='password_too_short',
            )
        if not any(char.isdigit() for char in password):
            raise ValidationError(
                _("This password must contain at least one digit."),
                code='password_no_digit',
            )
        if not any(char.isalpha() for char in password):
            raise ValidationError(
                _("This password must contain at least one letter."),
                code='password_no_letter',
            )
