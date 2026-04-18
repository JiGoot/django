from datetime import timedelta
import json
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from common.authentication import BranchManagerAuth
from core.utils import formattedError
from order.models.order import Order
from django.db import transaction
from django.utils import timezone
import logging



logger = logging.getLogger(name=__file__)


class Branch__AcceptOrder(APIView):
    """
    Branch manager can only accept its own order, and is allowed to add [delay] as well as to
    add items or remove from t
    """

    authentication_classes = [
        BranchManagerAuth,
    ]
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    itemFields = ("qty", "init_qty", "removed")
    fields = ("status", "ept", "subtotal", "accepted_at")

    def post(self, request, *args, **kwargs):
        """# INFO: we make use of order queryset [orders_qs] instead of [get] an instance
            # because i allow to efficiently and dynamicaly update an instance
        TODO: for the mean time branch can only change the quatity of an orderitem or remove it from the order
        later we can maybe give the branch ability to replace an orderitem with a new one
        """
        try:
            _ept = request.data.pop("ept", None)
            _items = request.data.pop("items", None)
            _branch = request.user.branch
            if not _branch:
                return Response(status=status.HTTP_404_NOT_FOUND)
            _order = _branch.orders.get_or_none(id=kwargs["orderID"])
            if not isinstance(_order, Order):
                return Response(status=status.HTTP_404_NOT_FOUND)
            if _order.status in [Order.Status.cancelled, Order.Status.delivered]:
                return Response("order terminated", status=status.HTTP_400_BAD_REQUEST)
            if not _order.status == Order.Status.placed:
                return Response(
                    "only placed orders can be accepted",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                if _items:
                    for itemData in json.loads(_items):
                        pk = itemData.pop("id", None)
                        cleanedData = {
                            key: value
                            for key, value in itemData.items()
                            if key in self.itemFields
                        }
                        _order.items.filter(id=pk).update(**cleanedData)
                    _order.subtotal = _order.recalculate_subtotal()
                _order.status = Order.Status.accepted
                if _ept:
                    _order.ept = timedelta(minutes=_ept)
                    _order_ept_minutes = _order.ept.total_seconds() / 60
                    # NOTE:: NOtify
                    if 0 < (_ept / _order_ept_minutes) > 0.1:
                        # TODO:: Notify the customer  if the adjustment exceed 10% of the initial ept
                        # “Your order's preparation time has been adjusted due to kitchen workload.”
                        pass

                _order.accepted_at = timezone.now()
                _order.save(update_fields=self.fields)

                # TODO: start or triger dispatcher
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
