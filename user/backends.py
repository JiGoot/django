
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, dial_code=None, phone=None, **kwargs):
        user = None

        # 1. Try email login
        if email:
            try:
                user = UserModel.objects.get(email=email)
            except UserModel.DoesNotExist:
                pass

        # 2. Try phone login if email didn't work
        if not user and dial_code and phone:
            try:
                user = UserModel.objects.get(dial_code=dial_code, phone=phone)
            except UserModel.DoesNotExist:
                return None

        if user and user.check_password(password):
            return user

        return None
