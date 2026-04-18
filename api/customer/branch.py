import logging
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from api.customer.apiview import CustomerAPIView
from branch.models.branch import Branch
from branch.models.delivery_type import DeliveryType
from branch.models.shift import Shift
from branch.serializers.branch import BranchSrz
from common.models import City
from rest_framework_simplejwt.authentication import JWTAuthentication
from common.serializers.city import CitySrz
from core.utils import formattedError
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.db.models import Prefetch

# Define a custom ordering function for categories
# Create a logger for this file
logger = logging.getLogger(__name__)


class Customer__GetBranch(CustomerAPIView):
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
            branch = (
                Branch.objects.select_related("supplier", "supplier__country")
                .prefetch_related(
                    Prefetch(
                        "delivery_types",  # the related name on Branch
                        queryset=DeliveryType.objects.filter(is_active=True),
                        to_attr="active_delivery_types",  # optional: store in a custom attribute
                    ),
                    Prefetch(
                        "shifts",  # the related name on Branch
                        queryset=Shift.objects.filter(is_active=True),
                        to_attr="active_shifts",  # optional: store in a custom attribute
                    ),
                    # Prefetch("")
                    # "supplier__tags",
                )
                .get(id=_id)
            )
            return Response(BranchSrz.Customer.default(branch), status=status.HTTP_200_OK)
        except (ValueError, ObjectDoesNotExist) as e:
            logger.warning(formattedError(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(formattedError(e))
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
