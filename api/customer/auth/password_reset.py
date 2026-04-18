from django.core.signing import TimestampSigner, SignatureExpired
from django.core.signing import Signer, BadSignature
from django.contrib.auth.hashers import make_password
from datetime import timedelta
import logging
from api.customer.apiview import CustomerAPIView
from customer.models.customer import Customer
from core import verify
from core.utils import formattedError
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.core.cache import cache

from user.models import User

logger = logging.getLogger(name=__file__)

PASSWORD_RESET_TOKEN_EXPIRY = timedelta(minutes=10).total_seconds()


class CustomerRequestPasswordReset(CustomerAPIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        _dial_code = request.data.get('dial_code')
        _phone = request.data.get('phone')

        try:
            if not all([_dial_code, _phone]):
                raise ValueError("Le numéro de téléphone et son indicatif sont requis.")

            user: User = User.objects.only('id').filter(dial_code=_dial_code, phone=_phone).first()
            if user:
                # Avoid re-sending if OTP is already cached
                if not cache.get(user.phone_otp_cache_key):
                    # publisher.publish(verify.OTP.send, user.phone_otp_cache_key, user.dial_code, user.phone)
                    pass
            # Always return 200 to avoid leaking whether the user exists
            return Response(status=status.HTTP_200_OK)

        except ValueError as e:
            logger.warning(formattedError(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerVerifyPasswordRest(CustomerAPIView):
    '''
    API endpoint that verifies OTP for password reset.
    '''
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        _dial_code = request.data.get('dial_code', None)
        _phone = request.data.get('phone', None)
        _code = request.data.get('code', None)

        try:
            if not all([_dial_code, _phone, _code]):
                raise ValueError("Toutes les informations sont requises.")

            user: User = User.objects.only('id').filter(dial_code=_dial_code, phone=_phone).first()
            cached_code = cache.get(user.phone_otp_cache_key) 

            if not cached_code:
                raise ValueError("Demande de réinitialisation invalide ou expirée.")
            if str(cached_code) != str(_code):
                raise ValueError("Code de vérification invalide ou expiré")

            # Hash the user_id
            signer = TimestampSigner()
            signed_user_id = signer.sign(user.id)

            cache.delete(user.phone_otp_cache_key)  # Cleanup
            return Response({"token": signed_user_id}, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.warning(formattedError(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerPasswordReset(CustomerAPIView):
    '''
    API endpoint that allows simultaneous phone verification and customer account creation.
    '''
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        _token = request.data.get('token', None)
        _new_password = request.data.get('password')

        try:
            if not all([_token,  _new_password]):
                raise ValueError("Toutes les informations sont requises.")

            signer = TimestampSigner()
            try:
                user_id = signer.unsign(_token, max_age=PASSWORD_RESET_TOKEN_EXPIRY)
            except SignatureExpired:
                raise ValueError("Le lien de réinitialisation a expiré.")
            except BadSignature:
                raise ValueError("Jeton de réinitialisation invalide ou altéré.")

            Customer.password_validator(_new_password)  # reuse your validation logic

            user: User = User.objects.get(id=user_id)
            user.set_password(_new_password)
            user.save(update_fields=['password'])
            return Response(status=status.HTTP_200_OK)

        except ValueError as e:
            logger.warning(str(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
