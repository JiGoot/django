"""[⎷][⎷][⎷]
* paginaton: YES
[_published] - allow to send to the customer user, only data of published kitchens.
thiis should be done everywhere kitchen data is send to the customer
[_tags] - allow to fecth kitchen according to user preferences
"""

import logging
from time import sleep

# from turfpy.measurement import Polygon
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from api.customer.apiview import CustomerAPIView
from common.models import City, Zone
from common.serializers.zone import ZoneSrz
from core.utils import formattedError

from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.cache import cache

# from turfpy.measurement import boolean_point_in_polygon

# Create a logger for this file
logger = logging.getLogger(__name__)


import logging
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from api.customer.apiview import CustomerAPIView
from branch.models.branch import Branch
from branch.serializers.branch import BranchSrz
from common.models import City, Zone
from common.serializers.zone import ZoneSrz
from common.serializers.city import CitySrz
from core.utils import formattedError
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache

# Define a custom ordering function for categories
# Create a logger for this file
logger = logging.getLogger(__name__)


class Customer__GetZone(CustomerAPIView):
    """[⎷][⎷][⎷]
    * pagination : NO
    Return a list of a given kitchen's items arranged by category
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        try:
            _id = kwargs.get("id", None)
            # TODO:: Get city from cache if possible , to invalidate using django signals
            zone: Zone = Zone.objects.select_related("city").get(id=_id)
            return Response(ZoneSrz.map(zone), status=status.HTTP_200_OK)
        except (ValueError, ObjectDoesNotExist) as e:
            logger.warning(formattedError(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(formattedError(e))
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MapGeometryData(CustomerAPIView):
    """
    Allow to retreive the list of zones within a given country and city
    REQUIRED query parameters:
        - country_code
        - city
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    class Cached:
        @classmethod
        def active_city_zones(cls, city_id):
            return f"customer::active__{city_id}_zones::"

    def get(self, request, **kwargs):
        try:
            # required in the customer app
            city_id = request.query_params.get("city_id", 1)  # Default to kinshasa

            """Handle cache"""
            # cached_key = self.Cached.active_city_zones(city_id)
            # cached = cache.get(cached_key)
            # try:
            #     if cached:
            #         cached["cached"] = True
            #         return Response(cached, status=status.HTTP_200_OK)
            # except Exception as e:
            #     logger.warning(formattedError(e))

            """Compute logic"""
            city: City = City.objects.get(id=city_id)
            zones = Zone.objects.filter(city=city, is_active=True)
            # TODO: Make a breaking change by returning only `ZoneSrz.map(zones)` as payload
            payload = {
                "bbox": city.bbox,
                "zones": ZoneSrz.map(zones),
            }
            # cache.set(cached_key, payload, timeout=30 * 60)  # or None for permanent
            return Response(
                payload,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception(formattedError(e))
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
