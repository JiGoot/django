from api.customer.apiview import CustomerAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import permissions, status
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.response import Response
from core.utils import formattedError
import logging

from order.models.order import Order
from order.serializers.order import OrderSrz

logger = logging.getLogger(name=__file__)


class Customer__GetOrder(CustomerAPIView):
    authentication_classes = [
        JWTAuthentication,
    ]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        try:
            _id = int(kwargs["id"])
            _order = Order.objects.select_related("branch").get(
                id=_id, customer=request.user
            )
            return Response(
                OrderSrz.Customer.default(_order), status=status.HTTP_200_OK
            )
        except (ValueError, Order.DoesNotExist) as e:
            logger.warning(formattedError(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(
                formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
