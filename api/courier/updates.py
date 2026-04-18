from datetime import datetime, timedelta
import logging
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.utils import CourierStatus, formattedError
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from courier.authentication import CourierAuthentication
from courier.models import Courier, CourierShift
from courier.serializers import CourierSrz
from django.utils import timezone
import pytz

# Create a logger for this file
logger = logging.getLogger(__name__)
class Courier__StatusUpdate(APIView):

    '''The kitchen self update, is when a kitchen or kitchen's manager update some of its properties.
    For security reason a kitchen manager can not update any kitchen properties, only those related to its operatios'''
    authentication_classes = [CourierAuthentication,]
    permission_classes = [permissions.IsAuthenticated,]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, **kwargs):
        try:
            _status = kwargs['status']
            courier = request.user.courier
            # Ensure the user is a Courier instance
            if not isinstance(courier, Courier):
                raise Exception("Invalid user")
            tz = pytz.timezone(courier.city.timezone)  # e.g. "Africa/Kinshasa"
            local_now = timezone.now().astimezone(tz)
            # Get the active shift for the courier
            _shift = courier.active_shift()
            if isinstance(_shift, CourierShift):  # INFO:: WITH ACTIVE SHIFT
                if courier.status == Courier.Status.offline:
                    if _status == courier.status:
                        return Response(status=status.HTTP_200_OK)
                    elif _status == Courier.Status.online:
                        if (local_now - _shift.start_dt).total_seconds() < 10 * 60:
                            courier.status = Courier.Status.online
                            courier.paused_at = None
                            courier.save(update_fields=('status', 'paused_at'))
                        else:
                            task_name = "cancel_shift {_shift.pk}"
                            # async_task(_shift.cancel_shift, _shift.pk, task_name= task_name) 
                            raise ValidationError(
                                "Not allowed after the first 10 minutes of the shift start.")
                    else:
                        raise ValidationError(
                            "Cannot pause when current satus is off-line.")                
                else: # INFO When current courier status is not off-line
                    if _status == Courier.Status.online:
                        if _status == courier.status:
                            return Response(status=status.HTTP_200_OK)
                        courier.status = _status
                        courier.paused_at = None
                        courier.save(update_fields=('status', 'paused_at'))
                    elif _status == Courier.Status.paused:
                        # if courier.status == _status:
                        if courier.paused_at != None:
                            time_since_paused = timezone.now() - courier.paused_at
                            if courier.paused_at and time_since_paused.total_seconds() < 10 * 60:
                                courier.status = _status
                                courier.save(update_fields=('status',))
                                return Response(CourierSrz.Courier.default(courier), status=status.HTTP_200_OK)
                        with transaction.atomic():
                            courier.status = _status
                            courier.paused_at = timezone.now()
                            courier.save(update_fields=('status', 'paused_at'))
                            # INFO:: Update shift
                            _shift.pause_count += 1
                            _shift.save(update_fields=('pause_count',))
                    elif _status == Courier.Status.offline:
                        task_name = "cancel_shift {_shift.pk}"
                        if courier.status == _status:  # Status already offline
                            # async_task(_shift.cancel_shift, task_name= task_name) 
                            return Response(CourierSrz.Courier.default(courier), status=status.HTTP_200_OK)
                        with transaction.atomic():
                            courier.status = _status
                            courier.paused_at = None
                            courier.save(update_fields=('status', 'paused_at'))
                            # async_task(_shift.cancel_shift, task_name= task_name) 
            else:  # WITHOUT ACTIVE SHIFT
                assert _status == Courier.Status.offline,"Missing an active shift."
                courier.status = _status
                courier.paused_at = None
                courier.save()
            data = CourierSrz.Courier.default(courier)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception(formattedError(exc))
            if isinstance(exc, ValidationError):
                return Response(exc.messages.pop(), status=status.HTTP_400_BAD_REQUEST)
            return Response(str(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# class Courier__SelfUpdate(APIView):

#     '''The kitchen self update, is when a kitchen or kitchen's manager update some of its properties.
#     For security reason a kitchen manager can not update any kitchen properties, only those related to its operatios'''
#     authentication_classes = [CourierAuthentication,]
#     permission_classes = [permissions.IsAuthenticated,]
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]

#     def post(self, request):
#         try:
#             _fields = {
#                 key: timedelta(seconds=value) for key, value in request.data.items() if key in ['ept', 'delay', ]
#             }
#             # # Allow updates of only fields under manager clearance
#             # _fields = {
#             #     key: value for key, value in request.data.items() if key in ['ept', 'delay', ]
#             # }
#             # # Format seconds in [timedelta] for duration field such as [ept] and [delay]
#             # if _fields.__contains__('ept'):
#             #     _value = _fields['ept']
#             #     _fields['ept'] = timedelta(seconds=_value)
#             # if _fields.__contains__('delay'):
#             #     _value = _fields['delay']
#             #     _fields['delay'] = timedelta(seconds=_value)
#             # INFO :: Run the self update
#             Courier.objects.filter(id=request.user.courier.id).update(**_fields)
#             return Response(KitchenSrz.FoodBusiness.default(request.user.kitchen), status=status.HTTP_200_OK)
#         except Exception as e:
#             logger.exception(formattedError(e))
#             return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
