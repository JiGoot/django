import logging
from django.db import transaction
from core.utils import formattedError
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from courier.authentication import CourierAuthentication
from courier.models import Courier
from order.models.order import Order
# Create a logger for this file
logger = logging.getLogger(__name__)

class Courier__AcceptOffer(APIView):
    '''The kitchen self update, is when a kitchen or kitchen's manager update some of its properties.
    For security reason a kitchen manager can not update any kitchen properties, only those related to its operatios'''
    authentication_classes = [CourierAuthentication,]
    permission_classes = [permissions.IsAuthenticated,]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, **kwargs):
        try:
            _lat = request.query_params.get('lat', None)
            _lng = request.query_params.get('lng', None)
            order_id = kwargs['order_id']
            courier = request.user.courier
            if not isinstance(courier, Courier):
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            order = Order.objects.get_or_none(id=order_id)
            if not isinstance(order, Order):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            with transaction.atomic():
                courier.update_coords(_lat, _lng) if _lat and _lng else None
                order.courier = courier
                # TODO:: #nextVersion see if you can update courier acceptance rate
                # TODO:: #nextVersion see if it is relevent to notify either cient or kitchen
                order.save(update_fields=('courier',))
            data = {
                # "utc_diff": utcDiff
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception(formattedError(exc))
            return Response(formattedError(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class Courier__DeclineOffer(APIView):

#     '''The kitchen self update, is when a kitchen or kitchen's manager update some of its properties.
#     For security reason a kitchen manager can not update any kitchen properties, only those related to its operatios'''
#     authentication_classes = [CourierAuthentication,]
#     permission_classes = [permissions.IsAuthenticated,]
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]

#     def post(self, request):
#         try:
#             # Allow updates of only fields under manager clearance
#             allowed_fields = {
#                 key: value for key, value in request.data.items()
#                 if key in ['ept', 'delay', ]
#             }
#             # Format seconds in [timedelta] for duration field such as [ept] and [delay]
#             if allowed_fields.__contains__('ept'):
#                 _value = allowed_fields['ept']
#                 allowed_fields['ept'] = timedelta(seconds=_value)
#             if allowed_fields.__contains__('delay'):
#                 _value = allowed_fields['delay']
#                 allowed_fields['delay'] = timedelta(seconds=_value)
#             # INFO :: Run the self update
#             FoodBusiness.objects.filter(manager=request.user).update(
#                 **allowed_fields)
#             return Response(KitchenSrz.Courier.default(request.user.courier), status=status.HTTP_200_OK)
#         except Exception as e:
#             logger.exception(formattedError(e))
#             return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
