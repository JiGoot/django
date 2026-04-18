
from django.utils import timezone
import pytz

from common.models.slot import  Slot


from datetime import date, datetime
import logging
from common.serializers.slots import SlotSrz


from core.utils import formattedError
from django.db.models import Min, Max, Q, Count

from courier.authentication import CourierAuthentication
from courier.models.courier import Courier
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

# Create a logger for this file
logger = logging.getLogger(__name__)



class Courier__Slots(APIView):
    authentication_classes = [CourierAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, **kwargs):
        try:
            courier: Courier = request.user
            # Get city timezone, assume city has a timezone field
            city_tz = pytz.timezone(courier.city.timezone) 
            local_city_now = timezone.now().astimezone(city_tz)
            local_city_date = local_city_now.date()

            # Annotate slots with shift count for today in that city
            # TODO:: Filter slots by city delivery window
            # TODO:: cache by city and date
            slots = Slot.objects.annotate(
                capacity=Count(
                    "shifts",
                    filter=Q(shifts__start__date=local_city_date)
                )
            )
            return Response(SlotSrz.default(slots), status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception(formattedError(exc))
            return Response(str(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)



