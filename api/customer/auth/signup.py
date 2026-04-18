import re
import time
from django.contrib.auth.hashers import make_password
from datetime import timedelta
import logging
from api.customer.apiview import CustomerAPIView
from customer.models.customer import Customer, CustomerDevice
from customer.serializers import CustomerSrz
from core import settings, verify
from core.utils import Gender, formattedError
from django.core.exceptions import ValidationError
from django.db import transaction
from django_ratelimit.decorators import ratelimit
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.core.cache import cache
from core.rabbitmq.broker import publisher
from user.models import User

logger = logging.getLogger(name=__file__)


class CustomerSignupRequest(CustomerAPIView):
    permission_classes = [
        permissions.AllowAny,
    ]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        _name = request.data.get("name", None)
        _gender = request.data.get("gender", None)
        _dial_code = request.data.get("dial_code", None)
        _phone = request.data.get("phone", None)
        _password = request.data.get("password", None)
        _channel = request.data.get("channel", "sms")
        try:
            if not all([_name, _dial_code, _phone, _password]):
                raise ValueError("Le nom, le numéro de téléphone et le mot de passe sont requis.")
            if _gender and _gender not in Gender.values:
                raise ValueError(f"Genre invalide. Veuillez choisir {Gender.values}.")
            if User.objects.filter(dial_code=_dial_code, phone=_phone).exists():
                raise ValueError("Un compte avec ce numéro existe déjà. Essayez de vous connecter.")

            Customer.password_validator(_password)

            otp = verify.OTP(_dial_code, _phone)
            signup_key = f"signup:{_dial_code}{_phone}_v{int(time.time())}"
            user_data = {
                "name": _name,
                "gender": _gender,
                "dial_code": otp.dial_code,
                "phone": otp.phone,
                "password": make_password(_password),  # Hash before storing if needed
            }

            # Register a signup request. OTP will need to be confirm within 10 minute
            cache.set(signup_key, user_data, timeout=timedelta(minutes=10).total_seconds())

            # INFO:: Avoids re-sending the OTP if One was already sent (otp.cacheKey), and
            # If an OTP was already sent, don't resend it
            if cache.get(otp.cacheKey):
                return Response(
                    {
                        "msg": "Un code a déjà été envoyé.",
                        "signup_key": signup_key,
                    },
                    status=status.HTTP_200_OK,
                )

            # Otherwise send a new OTP
            publisher.publish(otp.send, otp.dial_code, otp.phone)

            return Response(
                {
                    "signup_key": signup_key,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, (AssertionError, ValueError)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerSignUp(CustomerAPIView):
    """
    API endpoint that allows simultaneous phone verification and customer account creation.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        _signup_key = request.data.get("signup_key", None)
        _code = request.data.get("code", None)
        _fcm = request.data.get("fcm", None)
        _device = request.data.get("device", "Unknown").strip()

        try:
            if not all([_signup_key, _code]):
                raise ValueError("Requette invalide")

            user_data = cache.get(_signup_key)
            if not user_data:
                # INFO:: Return 410 status to improve feedback when signup_key or otp.cacheKey is missing
                return Response(
                    "Votre demande d’inscription a expiré. Veuillez recommencer la procédure.",
                    status=status.HTTP_410_GONE,
                )

            # INFO:: OTP Verify
            otp = verify.OTP(user_data["dial_code"], user_data["phone"])
            cached_code = cache.get(otp.cacheKey)

            if not _code or str(cached_code) != str(_code):
                raise ValueError("Code de vérification invalide ou expiré")

            with transaction.atomic():
                user, create = User.objects.get_or_create(
                    dial_code=user_data["dial_code"], phone=user_data["phone"]
                )
                user.name = user_data["name"]
                user.gender = user_data["gender"]
                user.password = user_data["password"]
                user.save(update_fields=["name", "gender", "password"])
                # Create a customer profile
                customer: Customer = Customer.objects.create(user=user)
                # Create the customer Token, simplifying the process by signing up and loging in in the sasme time,
                device, created = CustomerDevice.objects.get_or_create(fcm=_fcm)
                device.customer = customer
                device.device = _device
                device.platform = _platform
                device.save()
                cache.delete(_signup_key)  # Cleanup

            data = CustomerSrz.Customer.default(customer)
            # data["token"] = token.key
            return Response(data, status=status.HTTP_200_OK)
        except ValueError as e:
            logger.warning(formattedError(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error(formattedError(exc))
            if isinstance(exc, ValidationError):
                return Response(exc.messages.pop(), status=status.HTTP_400_BAD_REQUEST)
            return Response(str(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
