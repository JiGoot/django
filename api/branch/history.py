from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from branch.models.branch import Branch
from common.authentication import BranchManagerAuth
from core.utils import  formattedError
from django.core.paginator import Paginator, EmptyPage
import logging
from common.authentication import BranchManagerAuth
from order.models.order import Order
from order.serializers.order import OrderSrz


# Create a logger for this file
logger = logging.getLogger(__name__)

from django.db.models import Case, When, IntegerField
from django.db.models.functions import Greatest

exclude_status = [
    Order.Status.placed,
    Order.Status.accepted,
    Order.Status.ready,
]

status_priority = {
    Order.Status.picked_up: 1,
    Order.Status.delivered: 2,
    Order.Status.cancelled: 3,  # optional
}


class Branch__History(APIView):
    authentication_classes = [BranchManagerAuth]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    DEFAULT_PAGE_SIZE = 15
    MAX_PAGE_SIZE = 100

    def get(self, request, *args, **kwargs):
        allowed_status = [
            Order.Status.picked_up,
            Order.Status.delivered,
            Order.Status.cancelled,
        ]

        try:
            # Validate and get pagination parameters with defaults

            page_index = int(request.query_params.get("page", 1))
            page_size = min(
                int(request.query_params.get("page_size", self.DEFAULT_PAGE_SIZE)),
                self.MAX_PAGE_SIZE,
            )
            if page_index < 1:
                raise ValueError("Page must be a positive integer")

            manager = request.user
            branch: Branch = manager.branch
            if not branch:
                raise ValueError("Unsuported branch type")

            # Single query with conditional filtering
            qs = (
                Order.objects.filter(branch=branch, status__in=allowed_status)
                .annotate(
                    status_rank=Case(
                        *[When(status=s, then=v) for s, v in status_priority.items()],
                        default=999,
                        output_field=IntegerField(),
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
                .order_by("status_rank", "-updated_at")
            )

            paginator = Paginator(qs, 15)  # TODO us [DEFAULT_PAGE_SIZE]
            orders = paginator.page(page_index)

            data = {
                "pagination": {
                    "count": paginator.count,
                    "total_pages": paginator.num_pages,
                    "current_page": orders.number,
                    "has_next": orders.has_next(),
                },
                "orders": OrderSrz.Branch.listTile(orders),
            }
            return Response(data, status=status.HTTP_200_OK)

        except (AssertionError, ObjectDoesNotExist) as e:
            logger.warning(formattedError(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Unexpected error in branch history: {formattedError(e)}")
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

