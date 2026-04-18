from rest_framework.throttling import AnonRateThrottle, UserRateThrottle, ScopedRateThrottle
import logging

from rest_framework import permissions, status
from api.customer.apiview import CustomerAPIView
from common.models.boundary.city import City
from common.models.city_service import CityService
from common.serializers.vertical_type import CityServiceSrz, ServiceSrz
from core.utils import formattedError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication


# Create a logger for this file
logger = logging.getLogger(__name__)
import pytz, h3


class Customer__VerticalTypes(CustomerAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        try:
            # --- PARAMS ---
            _city_id = kwargs.get("city_id", 1)  # Default to kinshasa
            city: City = City.objects.get(id=_city_id)
            # return Response(city.cached.vertical_types, status=status.HTTP_200_OK)
            return Response(
                CityServiceSrz.Customer.default(
                    CityService.objects.filter(city=city, is_active=True).select_related("service")
                ),
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, (ValueError, ObjectDoesNotExist)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
