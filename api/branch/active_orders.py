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
from django.db.models.functions import Now, Coalesce

# Create a logger for this file
logger = logging.getLogger(__name__)


class Branch__ActiveOrders(APIView):
    authentication_classes = [BranchManagerAuth]
    permission_classes = [permissions.BasePermission]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]


    def get(self, request, *args, **kwargs):
        manager = request.user
        branch: Branch = manager.branch

        try:
            if not branch:
                raise ValueError("unassigned branch")

            return Response(branch.cached.active_orders(), status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, (AssertionError, ObjectDoesNotExist)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(
                formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
