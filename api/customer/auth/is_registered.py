import logging
from api.customer.apiview import CustomerAPIView
from customer.models.customer import Customer
from core.utils import formattedError
from django.core.exceptions import ValidationError
from django_ratelimit.decorators import ratelimit
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.core.cache import cache

from user.models import User

logger = logging.getLogger(name=__file__)


class Customer__Registerd(CustomerAPIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        try:
            _dialCode = request.data.get('dial_code')
            _phone = request.data.get('phone')
            if (not _dialCode or not _phone):
                raise ValueError("Format du telphone invalide")
            _customer = Customer.objects.get(
                user__dial_code=_dialCode, user__phone=_phone.lstrip('0'))
            if not _customer:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, ValueError):
                return Response(formattedError(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

