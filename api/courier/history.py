from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from core.utils import formattedError
from courier.authentication import CourierAuthentication
from courier.serializers import CourierSrz

from django.core.paginator import Paginator
import logging
from order.models.order import Order

from order.serializers.order import OrderSrz

# Create a logger for this file
logger = logging.getLogger(__name__)


class Courier__OrdersHistory(APIView):
    authentication_classes = [CourierAuthentication,]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        try:
            _pageId = int(request.query_params.get('page', None))
            _page_size = int(request.query_params.get('page_size', 15))
            _courier = request.user.courier
            _orders = Order.objects.select_related('customer', "courier", 'cancelled')\
                .filter(courier=_courier, status=[Order.Status.delivered, Order.Status.cancelled])\
                .exclude()\
                .order_by('-created_at')  # froma last-to-first
            # NOTE ----- Pagination -----
            paginator = Paginator(_orders, _page_size)
            if _pageId:
                if paginator.num_pages >= int(_pageId):
                    page = paginator.page(_pageId)
                    _orders = page.object_list
                else:  # NOTE No more page
                    _orders = Order.objects.none()
            # NOTE ----- Response -----
            data = {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "has_next": _pageId < paginator.num_pages,
                "courier": CourierSrz.Courier.default(_courier),
                "results": OrderSrz.Courier.listTile(_orders),
            } 

            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
