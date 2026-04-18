from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from common.authentication import BranchManagerAuth
from core.utils import formattedError
import logging
from common.authentication import BranchManagerAuth
from order.models import Order, OrderItem
from order.serializers.item import OrderItemSrz
from order.serializers.order import OrderSrz
from django.db.models import Case, When, F, Value, IntegerField, DurationField
from django.db.models.functions import Now, Coalesce, Greatest

# Create a logger for this file
logger = logging.getLogger(__name__)


class Branch__GetOrder(APIView):
    authentication_classes = [BranchManagerAuth]
    permission_classes = [permissions.BasePermission]
    throttle_classes = [UserRateThrottle]

    def get(self, request, *args, **kwargs):
        try:
            order: Order = (
                Order.objects.prefetch_related("items", "payments")
                .select_related("customer", "courier")
                .defer("branch")
                .annotate(
                    urgency_score=Case(
                        When(placed_at__lt=Now() - F("ept"), then=Value(3)),
                        When(status="placed", then=Value(2)),
                        When(status="accepted", then=Value(1)),
                        When(status="ready", then=Value(0)),
                        output_field=IntegerField(),
                    ),
                    time_in_status=Case(
                        When(status="placed", then=Now() - F("placed_at")),
                        When(
                            status="accepted",
                            then=Now() - Coalesce(F("accepted_at"), F("placed_at")),
                        ),
                        When(
                            status="ready",
                            then=Now() - Coalesce(F("ready_at"), F("placed_at")),
                        ),
                        output_field=DurationField(),
                    ),
                    updated_at=Greatest(
                        "placed_at",
                        "accepted_at",
                        "ready_at",
                        "pickedup_at",
                        "delivered_at",
                        "cancelled_at",
                    ),
                )
                .get(id=kwargs["orderID"])
            )
            data = OrderSrz.Branch.default(order)
            data["items"] = OrderItemSrz.default(order.items.all())
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, AssertionError) or isinstance(e, ObjectDoesNotExist):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(
                formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
