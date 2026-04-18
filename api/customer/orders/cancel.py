from api.customer.apiview import CustomerAPIView
from common.models.catalog.variant import Variant
from order.models.order import Order
from order.notify import OrderNotify
from core.rabbitmq.broker import publisher
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import permissions, status
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.response import Response
from core.utils import CancelledBy, CancelledReason, formattedError
from django.db import transaction
import logging



logger = logging.getLogger(name=__file__)


class Customer__OrderCancel(CustomerAPIView):
    authentication_classes = [JWTAuthentication,]
    permission_classes = [permissions.IsAuthenticated,]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                # STEP:: 1 - Get order
                order: Order = (
                    Order.objects
                    .select_for_update()
                    .prefetch_related('items')
                    .get(id=kwargs['id'], customer=request.user)
                )

                # STEP:: 2 - Permission Checks
                if order.terminated:
                    raise ValueError('Order already terminated')
                elif order.status != Order.Status.placed:
                    raise ValueError("Please contact our support team")  # Fixed: was 'return' instead of 'raise'

                # STEP:: 3 - Update order status
                order.status = Order.Status.cancelled
                order.save(update_fields=['status'])

                # STEP:: 4 - Stock Reversion
                for item in order.items.select_for_update():
                    variant: Variant = item.variant
                    variant.stock += item.qty
                    variant.save(update_fields=['stock'])

                # STEP:: 4 - Notify Relevant parties
                publisher.publish(OrderNotify.Branch.on_cancelled, order.id)
                if order.courier:
                    publisher.publish(OrderNotify.Courier.on_cancelled, order.id)
                    pass
                return Response("Successful", status=status.HTTP_200_OK)

        except (Order.DoesNotExist, ValueError) as e:
            logger.warning(str(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
