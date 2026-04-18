from typing import Optional, Union
from django.core.exceptions import ObjectDoesNotExist
from datetime import timedelta
import logging
from django.utils import timezone
import pytz
from branch.models.branch import Branch
from branch.models.shift import Shift
from branch.serializers.branch import BranchSrz
from branch.serializers.shift import ShiftSrz
from common.authentication import BranchManagerAuth
from core.utils import formattedError
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from django.core.exceptions import ValidationError

# Create a logger for this file
logger = logging.getLogger(__name__)


class Branch__StatusUpdate(APIView):
    """The branch self update, is when a branch or branch's manager update some of its properties.
    For security reason a kitchen manager can not update any branch properties, only those related to its operatios
    """

    authentication_classes = [
        BranchManagerAuth,
    ]
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request):
        try:
            # TODO add a StoreStatusRecord
            _status = request.data.get("status", None)
            _delay = request.data.get("delay", None)
            _reason = request.data.get("reason", None)
            branch: Branch = request.user.branch

            tz = pytz.timezone(branch.city.timezone)  # e.g. "Africa/Kinshasa"
            local_now = timezone.now().astimezone(tz)
            local_weekday = local_now.isoweekday()  # 1 = Monday
            shifts = Shift.objects.filter(branch=branch, weekdays__contains=[local_weekday], is_active=True)

            if _status == Branch.Status.open:
                branch.status = Branch.Status.open
                branch.delay_duration = None
                branch.delay_start = None
                # _store.closed_reason = None
                if not shifts:
                    raise ValidationError("An active shift is required")
            elif _status == Branch.Status.busy:
                branch.status = Branch.Status.busy
                branch.delay_duration = timedelta(minutes=_delay if _delay else 30)
                branch.delay_start = timezone.now()
                branch.delay_reason = _reason
                if not shifts:
                    raise ValidationError("An active shift is required")
            elif _status == Branch.Status.closed:
                branch.status = Branch.Status.closed
                branch.delay_duration = None
                branch.delay_start = None
                branch.delay_reason = None
            else:
                raise ValidationError("Unsuported status")
            # _store.closed_reason = _closedReason
            branch.save(update_fields=["status", "delay_duration", "delay_start", "delay_reason"])
            branchData = BranchSrz.Branch.default(branch)
            branchData["shifts"] = ShiftSrz.default(shifts) if shifts else None
            return Response(branchData, status=status.HTTP_200_OK)
        except (ValidationError, ObjectDoesNotExist) as e:
            logger.warning(str(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
