from django.utils import timezone
from order.models.order import Order
from core.rabbitmq.broker import publisher
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from core.tasks.fcm import FCM_Notify
from core.utils import formattedError
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
import logging
from common.authentication import BranchManagerAuth


logger = logging.getLogger(name=__file__)


class Branch__CancelOrder(APIView):
    authentication_classes = [BranchManagerAuth]
    permission_classes = [permissions.BasePermission]

    def post(self, request, *args, **kwargs):
        """# INFO: we make use of order queryset [orders_qs] instead of [get] an instance
        # because i allow to efficiently and dynamicaly update an instance"""
        try:

            branch = request.user.branch
            with transaction.atomic():
                order: Order = (
                    branch.orders
                    .filter(id=kwargs["orderID"])
                    .select_related("courier")
                    .first()
                )
                if not order:
                    raise ValueError("Order not found")
                if order.status == Order.Status.delivered or order.terminated:
                    raise ValueError("Order already terminated")

                reason = request.data.get("reason")
                if not reason:
                    raise ValueError("Cancellation reason is required")

                order.status = Order.Status.cancelled
                order.cancelled_at = timezone.now()
                order.save(update_fields=("status", "cancelled_at"))

            publisher.publish(FCM_Notify.Customer.on_store_cancellation, order.id)
            if order.courier:
                publisher.publish(FCM_Notify.Courier.on_store_cancellation, order.id)
            return Response(status=status.HTTP_200_OK)
        except (ObjectDoesNotExist, ValueError) as e:
            logger.warning(str(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(
                formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
