from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import pytz
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from core.utils import formattedError

import logging
from courier.authentication import CourierAuthentication
from courier.models.courier import Courier
from courier.serializers import CourierShiftSrz, CourierSrz

# Create a logger for this file
logger = logging.getLogger(__name__)


class Courier__Profile(APIView):
    authentication_classes = [CourierAuthentication]
    permission_classes = [permissions.BasePermission]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    CACHE_TIMEOUT = 60  # in seconds (1 minute)

    # TODO:: Cache placed order by branch and use Order and BranchPayment signal to cleanup

    def get(self, request, *args, **kwargs):
        courier: Courier = request.user
        city_tz = pytz.timezone(courier.city.timezone)
        local_now = timezone.now().astimezone(city_tz)
        try:
            payload = CourierSrz.Courier.default(courier)
            payload["shifts"] = CourierShiftSrz.default(courier.cached.shifts(local_now)) 
            # CACHE:: - courier payload by id
            # CACHE-INVAL...:: on Courier update
            # CACHE:: - courier'shift by shift payload by id
            # CACHE-INVAL...:: on CourierShift update
            return Response(payload, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, (AssertionError, ObjectDoesNotExist)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
