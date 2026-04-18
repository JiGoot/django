import logging
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from api.customer.apiview import CustomerAPIView
from branch.models.branch import Branch
from branch.serializers.branch import BranchSrz
from common.models import City, Zone
from common.serializers.zone import ZoneSrz
from rest_framework_simplejwt.authentication import JWTAuthentication
from common.serializers.city import CitySrz
from core.utils import formattedError
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache

# Define a custom ordering function for categories
# Create a logger for this file
logger = logging.getLogger(__name__)


class CityCart(CustomerAPIView):
    """[⎷][⎷][⎷]
    * pagination : NO
    Return a list of a given kitchen's items arranged by category
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
    ]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        try:

            _branchId = request.query_params.get("branch_id", None)
            _zone: Zone = Zone.objects.select_related("city").get(id=kwargs["zone"])
            city: City = _zone.city

            data = {}
            data["city"] = CitySrz.default(_zone.city)
            data["zone"] = ZoneSrz.map(Zone.objects.filter(city=city))
            return Response(data, status=status.HTTP_200_OK)
        except (ValueError, ObjectDoesNotExist) as e:
            logger.warning(formattedError(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(formattedError(e))
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


