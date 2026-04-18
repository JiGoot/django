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
from core.utils import formattedError

import logging
from order.models.order import Order
from django.core.cache import cache

# Create a logger for this file
logger = logging.getLogger(__name__)


class Branch__Profile(APIView):
    authentication_classes = [BranchManagerAuth]
    permission_classes = [permissions.BasePermission]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    CACHE_TIMEOUT = 60  # in seconds (1 minute)

    # TODO:: Cache placed order by branch and use Order and BranchPayment signal to cleanup
    class Cached:
        @classmethod
        def shifts(cls, id):
            return f"branch::{id}::shifts"

    def get(self, request, *args, **kwargs):
        manager = request.user
        branch: Branch = manager.branch
        try:
            if not branch:
                raise ValueError("unassigned branch")

            """Handle cache"""
            cached_key = self.Cached.shifts(branch.id)
            cached = cache.get(cached_key)
            try:
                if cached:
                    return Response(cached, status=status.HTTP_200_OK)
            except Exception as e:
                logger.warning(formattedError(e))

            """Compute Logic"""
            # Single query with conditional filtering
            shifts = shift.Shift.objects.filter(branch=branch, is_active=True)

            payload = BranchSrz.Branch.default(branch)
            payload["shifts"] = ShiftSrz.default(shifts) if shifts else None
            # CACHE:: - Branch profile payload by id
            # CACHE-INVAL...:: on Courier update
            # CACHE:: - branch'shift by shift payload by id
            # CACHE-INVAL...:: on CourierShift update
            return Response(payload, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, (AssertionError, ObjectDoesNotExist)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
