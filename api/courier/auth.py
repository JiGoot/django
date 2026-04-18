import logging
from core import settings, verify
from django.core.cache import cache
from django.utils import timezone
from core.utils import CourierStatus, formattedError
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.utils import timezone
from courier.authentication import CourierAuthentication

from courier.serializers import CourierSrz

# Create a logger for this file
logger = logging.getLogger(__name__)


class Courier__Registerd(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        try:
            _dialCode = request.data['dial_code']
            _phone = request.data['phone']
            if _phone == None or _dialCode == None:
                return Response('Invalid phone number format', status=status.HTTP_400_BAD_REQUEST)
            _courier = Courier.objects.get_or_none(
                manager__dial_code=_dialCode, manager__phone=_phone.lstrip('0'))
            if (isinstance(_courier, Courier)):
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(f'Internal error occurred!', status=status.HTTP_500_INTERNAL_SERVER_ERROR)


'''[⎷][⎷][⎷]
For user Authentication because user interface require to provide a valid OTP instead 
of a password.
'''
OTP_REQUEST_LIMIT = 10 if (settings.DEBUG) else 2  # TODO Default should be 3


class Courier__RequestOTP(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle, UserRateThrottle, ScopedRateThrottle]
    throttle_scope = 'otp'

    def post(self, request):
        _dialCode = request.data.get('dial_code', None)
        _phone = request.data.get('phone', None)
        _locale = request.data.get('locale', 'fr')
        try:
            if _dialCode is None or _phone is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            _courier = Courier.objects.get_or_none(dial_code=_dialCode, phone=_phone)
            if not isinstance(_courier, Courier):
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            tel = f"+{_dialCode}{_phone}"
            if cache.get(tel) is None:
                raise
                # async_task(verify.OTP.Courier.send, _dialCode, _phone, locale=_locale)
            return Response(status=status.HTTP_200_OK)
        except Exception as exc:
            return Response(str(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Courier__VerifyOTP(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        _dialCode = request.data.get('dial_code', None)
        _phone = request.data.get('phone', None)
        _code = request.data.get('code', None)
        try:
            # TODO:: verify the number of attemt 3 (attemts max)
            # reinitialise the user attempt count when a request is made
            assert _dialCode and _phone and _code, "Phone number or OTP code missing."
            assert Courier.objects.get(dial_code=_dialCode, phone=_phone), "Invalid phone number"
            tel = f"+{_dialCode}{_phone}"
            if not verify.check(_dialCode, _phone,  _code):
                return Response("Invalid OTP code", status=status.HTTP_401_UNAUTHORIZED)
            cache.delete(tel)
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            if isinstance(e, AssertionError) or isinstance(e, ObjectDoesNotExist):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# TODO add rate limit 5/m

# @override_settings(ROOT_URLCONF=__name__)

class Courier__ResetPwd(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        _dial_code = request.data.get('dial_code', '243')
        _phone = request.data.get('phone', None)
        _pwd = request.data.get('password', None)
        try:
            _courier = Courier.objects.get_or_none(
                dial_code=_dial_code, phone=_phone)
            if not isinstance(_courier, Courier):
                return Response(status=status.HTTP_404_NOT_FOUND)
            _courier.set_password(_pwd)
            _courier.save(update_fields=('password', ))
            return Response(status=status.HTTP_200_OK)

        except Exception as exc:
            return Response(str(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
