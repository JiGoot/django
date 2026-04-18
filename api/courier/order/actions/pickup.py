from datetime import timedelta
import json
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from core.utils import formattedError
from courier.authentication import CourierAuthentication
from order.models.order import Order
from django.db import transaction
from django.utils import timezone
import logging


logger = logging.getLogger(name=__file__)


class Courier__OrderPickup(APIView):
    """
    Branch manager can only accept its own order, and is allowed to add [delay] as well as to
    add items or remove from t
    """

    authentication_classes = [CourierAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    fields = ("status", "ept", "subtotal", "pickedup_at")

    def post(self, request, *args, **kwargs):
        """# INFO: we make use of order queryset [orders_qs] instead of [get] an instance
            # because i allow to efficiently and dynamicaly update an instance
        TODO: for the mean time branch can only change the quatity of an orderitem or remove it from the order
        later we can maybe give the branch ability to replace an orderitem with a new one
        """
        try:
            _courier = request.user
            if not _courier:
                return Response(status=status.HTTP_404_NOT_FOUND)
            _order = _courier.orders.get_or_none(id=kwargs["orderID"])
            if not isinstance(_order, Order):
                return Response(status=status.HTTP_404_NOT_FOUND)
            if _order.status in [Order.Status.cancelled, Order.Status.delivered]:
                return Response("order terminated", status=status.HTTP_400_BAD_REQUEST)
            if not _order.status == Order.Status.ready:
                return Response(
                    "only ready orders can be picked up",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                _order.status = Order.Status.picked_up
                _order.pickedup_at = timezone.now()
                _order.save(update_fields=self.fields)

                # TODO: start or triger dispatcher
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
