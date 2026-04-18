# from django.core.exceptions import ValidationError
# from django.utils.translation import gettext as _


# class Manager_PSWValidator:
#     def __call__(self, password: str):
#         assert len(password) >= 8, "Password should have at least 8 characters."
#         assert any(char.isdigit() for char in password), "should have at least one digits"
#         assert any(char.islower() for char in password), "require at least one lowercase letter"
#         assert any(char.isupper() for char in password), "require at least one uppercase letter"


