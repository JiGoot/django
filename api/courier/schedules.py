"""[⎷][⎷][⎷]
* paginaton: YES
[_published] - allow to send to the customer user, only data of published kitchens.
thiis should be done everywhere kitchen kitchen data is send to the customer
[_tags] - allow to fecth kitchens according to user preferences
"""

from datetime import date, datetime
import logging
from common.serializers.slots import SlotSrz


from core.utils import CourierStatus, formattedError

from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Min, Max, Q

from courier.authentication import CourierAuthentication
from courier.models import Courier, CourierShift
from courier.serializers import CourierSrz, CourierShiftSrz
from core.utils import DashStatus
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

# Create a logger for this file
logger = logging.getLogger(__name__)


# class CourierShiftSlotsAPI(APIView):
#     """
#     Allow to retreive the list of zones within a given country and city
#     REQUIRED query parameters:
#         - country_code
#         - city
#     """

#     authentication_classes = [CourierAuthentication]
#     permission_classes = [permissions.IsAuthenticated]
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]

#     def get(self, request, **kwargs):
#         try:
#             _lat = request.query_params.get("lat", None)
#             _lng = request.query_params.get("lng", None)
#             courier = request.user
#             # NOTE::Asyncronously Update courier location at the time of request
#             # for dispach use.
#             courier.update_coords(_lat, _lng) if _lat and _lng else None
#             _datetime = datetime.strptime(kwargs["date"], "%Y-%m-%d")
#             _slots = courier.city.cached_date_couriershifts(_datetime.date())
#             data = SlotSrz.default(_slots)
#             return Response(data, status=status.HTTP_200_OK)
#         except Exception as exc:
#             logger.exception(formattedError(exc))
#             return Response(str(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Courier__Shifts(APIView):
    """
    Allow to retreive the list of zones within a given country and city
    REQUIRED query parameters:
        - country_code
        - city
    """

    authentication_classes = [CourierAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, **kwargs):
        try:
            _lat = request.query_params.get("lat", None)
            _lng = request.query_params.get("lng", None)
            courier:Courier = request.user
            courier.update_coords(_lat, _lng) if _lat and _lng else None
            data = CourierShiftSrz.default(courier.cached.shifts) 
            return Response(data, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception(formattedError(exc))
            return Response(str(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddDashShifts(APIView):
    """
    Allow to retreive the list of zones within a given country and city
    REQUIRED query parameters:
        - country_code
        - city
    """

    authentication_classes = [
        CourierAuthentication,
    ]
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, **kwargs):
        try:
            courier = request.user.courier

            if not (isinstance(courier, Courier)):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            _date = request.data.pop("date", None)
            _start = request.data.get("start", None)
            _end = request.data.get("end", None)

            if not courier.can_dash_now:  # TODO:: or acceptance rate is > x
                raise ValidationError("privileged courier only.")
            elif not _date or not _start or not _end:
                raise ValidationError(
                    "missing one of the following information (date, start, end)"
                )
            with transaction.atomic():
                CourierShift.objects.create(
                    courier=courier,
                    date=_date,
                    **request.data,
                    is_dash=True,
                    status=DashStatus.confirmed,
                )
                courier.status = Courier.Status.online
                courier.save(update_fields=("status",))
            data = CourierSrz.Courier.default(courier)
            return Response(data, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception(formattedError(exc))
            if isinstance(exc, ValidationError):
                return Response(exc.messages.pop(), status=status.HTTP_400_BAD_REQUEST)
            return Response(str(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddScheduleShifts(APIView):
    """
    Allow to retreive the list of zones within a given country and city
    REQUIRED query parameters:
        - country_code
        - city
    """

    authentication_classes = [
        CourierAuthentication,
    ]
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def _group_consecutive_slots(self, ids):
        sorted_ids = sorted(ids)
        grouped = []
        temp_group = [sorted_ids[0]]
        for i in range(1, len(sorted_ids)):
            if sorted_ids[i] == sorted_ids[i - 1] + 1:
                temp_group.append(sorted_ids[i])
            else:
                grouped.append(temp_group)
                temp_group = [sorted_ids[i]]
        grouped.append(temp_group)  # Add the last group
        return grouped

    def post(self, request, **kwargs):
        # TODO:: #nextVersion :: on abusiv use restrict the number of slots a courier can take in a day and an the above 6 days
        # Annotate each CourierShift with the count of related slots
        try:
            _date = request.data.pop("date", None)
            _slotsData = request.data.pop("slots", None)
            courier = request.user.courier
            if not (isinstance(courier, Courier)):
                return Response(status=status.HTTP_404_NOT_FOUND)
            if not _date and not _slotsData:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            # INFO:: Raise overlapping shift exception
            shifts = courier.cached_shifts.filter(Q(is_dash=False) & Q(date=_date))
            if shifts.filter(slots__in=_slotsData).exists():
                raise ValidationError("overlaping shifts.")
            with transaction.atomic():
                for slots in self._group_consecutive_slots(_slotsData):
                    range = (
                        courier.city.cached_date_couriershifts(_date)
                        .filter(id__in=slots)
                        .aggregate(earliest_start=Min("start"), latest_end=Max("end"))
                    )
                    start = range.get("earliest_start")
                    end = range.get("latest_end")
                    if shifts.filter(start__lt=end, end__gt=start).exists():
                        raise ValidationError("overlaping shifts.")
                    if start and end:
                        obj = CourierShift.objects.create(
                            courier=courier,
                            date=_date,
                            **request.data,
                            start=start,
                            end=end,
                        )
                        if isinstance(obj, CourierShift):
                            obj.slots.set(slots)
                data = CourierSrz.Courier.default(courier)
                return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception(formattedError(exc))
            if isinstance(exc, ValidationError):
                return Response(exc.messages.pop(), status=status.HTTP_400_BAD_REQUEST)
            return Response(str(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from django.utils import timezone
import pytz


class ShiftConfirmation(APIView):
    """
    Allow to retreive the list of zones within a given country and city
    REQUIRED query parameters:
        - country_code
        - city
    """

    authentication_classes = [
        CourierAuthentication,
    ]
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, **kwargs):
        try:
            courier = request.user.courier
            if not (isinstance(courier, Courier)):
                return Response(status=status.HTTP_404_NOT_FOUND)
            shiftID = kwargs.get("shift_id")
            shift = courier.cached_shifts.filter(id=shiftID).first()
            if not (isinstance(shift, CourierShift)):
                return Response(status=status.HTTP_404_NOT_FOUND)
            if shift.status == DashStatus.confirmed:
                return ValidationError("shift already confrmed")
            elif shift.status == DashStatus.cancelled:
                raise ValidationError("shift already cancelled")
            elif shift.status == DashStatus.pending:
                tz = pytz.timezone(self.city.timezone)  # e.g. "Africa/Kinshasa"
                local_now = timezone.now().astimezone(tz)
                start = datetime.combine(shift.date, shift.start)
                diff = (start - local_now).total_seconds() / 60
                if diff < 0 or diff > 30:
                    raise ValidationError("only within 30 min before shift start")
                elif diff > 0 and diff <= 30:
                    shift.status = DashStatus.confirmed
                    shift.save(update_fields=("status"))
            data = CourierSrz.Courier.default(courier)
            return Response(data, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception(formattedError(exc))
            if isinstance(exc, ValidationError):
                return Response(exc.messages.pop(), status=status.HTTP_400_BAD_REQUEST)
            return Response(str(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
