from django.db.models import Prefetch
from django.db.models import Q
from django.utils import timezone
import pytz
from branch.models import shift
from branch.models.branch import Branch
from branch.serializers.branch import BranchSrz
from branch.serializers.shift import ShiftSrz
from common.authentication import BranchManagerAuth
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from django.db.models import Count
from core.utils import formattedError

import logging
from order.models.order import Order
from order.serializers.order import OrderSrz
from django.db.models import Case, When, F, Value, IntegerField, DurationField
from django.db.models.functions import Now, Coalesce, Greatest

# Create a logger for this file
logger = logging.getLogger(__name__)


class Branch__DashBoard(APIView):
    model = Order
    authentication_classes = [BranchManagerAuth]
    permission_classes = [permissions.BasePermission]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    CACHE_TIMEOUT = 60  # in seconds (1 minute)

    # TODO:: Cache placed order by branch and use Order and BranchPayment signal to cleanup
    class CachedKeys:
        @classmethod
        def dashboard(cls, type, id, weekday):
            return f"api.{type}.dashboard_{id}, {weekday}"

    def get(self, request, *args, **kwargs):
        manager = request.user
        branch: Branch = manager.branch
        tz = pytz.timezone(branch.city.timezone)  # e.g. "Africa/Kinshasa"
        local_now = timezone.now().astimezone(tz)
        local_weekday = local_now.isoweekday()  # 1 = Monday

        cacheKey = self.CachedKeys.dashboard(branch.type, branch.id, local_weekday)

        try:
            if not branch:
                raise ValueError("unassigned branch")
            allowed_statuses = [
                Order.Status.placed,
                Order.Status.accepted,
                Order.Status.ready,
            ]
            # Single query with conditional filtering
            shifts = shift.Shift.objects.filter(
                branch=branch, weekdays__contains=[local_weekday], is_active=True
            )

            qs = (
                Order.objects.filter(branch=branch, status__in=allowed_statuses)
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
                .order_by("-urgency_score", "time_in_status")
            )
            qs = qs[:5]  # slicing applies LIMIT in SQL
            # Get counts in a single query
            counts = qs.aggregate(
                placed=Count("id", filter=Q(status=Order.Status.placed)),
                accepted=Count("id", filter=Q(status=Order.Status.accepted)),
                ready=Count("id", filter=Q(status=Order.Status.ready)),
            )

            branchData = BranchSrz.Branch.default(branch)
            branchData["shifts"] = ShiftSrz.default(shifts) if shifts else None
            data = {
                "count": counts,
                "branch": branchData,
                "orders": OrderSrz.Branch.listTile(qs),
            }

            response = Response(data, status=status.HTTP_200_OK)

            return response
        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, (AssertionError, ObjectDoesNotExist)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(
                formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
