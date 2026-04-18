from api.customer.apiview import CustomerAPIView
from common.models.slot import Slot
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from common.serializers.slots import SlotSrz
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import logging

from core.utils import formattedError
from rest_framework_simplejwt.authentication import JWTAuthentication
logger = logging.getLogger(name=__file__)

class Customer__ScheduleSlotList(CustomerAPIView):
    '''NOTE [⎷]
    - create order
    - subscribe user and skitchen to FCM channels of [#<order.pk>]  (may be optional we can simply send data directly via token)
    '''
    authentication_classes = [JWTAuthentication,]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    @method_decorator(cache_page(60 * 60, key_prefix='scheduled_slots') ) # Cache the response for 1 hour
    def get(self, request, **kwargs):
        try: 
            _slots = Slot.objects.filter(availabled=True)
            return Response(SlotSrz.default(_slots), status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response('Internal error occurred', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

