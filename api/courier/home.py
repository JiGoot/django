from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from branch.models.branch import Branch
from branch.serializers.branch import BranchSrz
from core.utils import formattedError
from courier.authentication import CourierAuthentication
from courier.models import Courier
from courier.serializers import CourierSrz
import logging
from order.models.order import Order

from order.serializers.order import OrderSrz

# Create a logger for this file
logger = logging.getLogger(__name__)


class Courier__HomeView(APIView):
    authentication_classes = [CourierAuthentication,]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request,  *args, **kwargs):
        try:
            _lat = request.query_params.get('lat', None)
            _lng = request.query_params.get('lng', None)
            courier = request.user.courier
            # NOTE::Asyncronously Update courier location at the time of request
            # for dispach use.
            if not isinstance(courier, Courier):
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
            courier.update_coords(_lat, _lng) if _lat and _lng else None
            # NOTE:: Get ongoing courier order not yet terminated
            _orders = Order.objects.filter(courier__id=courier.pk)\
                .exclude(status__in=[Order.Status.delivered, Order.Status.cancelled])\
                .order_by('created_at')  # from firs-to-last

            # NOTE:: Get online kitchen location place,cache for 5 minute using an object manager
            _kitchens = Branch.objects.none() if _orders else courier.city.cached.open_kitchenes

            data = {
                'live': {
                    'kitchens': BranchSrz.Courier.default(_kitchens),
                },
                'orders': OrderSrz.Courier.default(_orders),
                'courier': CourierSrz.Courier.default(courier),
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception(formattedError(exc))
            return Response(str(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
