from order.models.order import Order
from core.rabbitmq.broker import publisher
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from courier.dispatcher import CourierDispatcher
from common.authentication import BranchManagerAuth

from core.utils import formattedError
from django.db import transaction
from django.utils import timezone
import logging

logger = logging.getLogger(name=__file__)


class Branch__ReadyOrder(APIView):
    '''
    Branch manager can only mark an order as ready, and is allowed to add [delay] as well as to
    add items or remove from 
    '''
    authentication_classes = [ BranchManagerAuth,]
    permission_classes = [permissions.IsAuthenticated,]
    throttle_classes = [UserRateThrottle]

    def post(self, request, *args, **kwargs):
        '''
        NOTE - EPT can be modified only by starting a busy mode, or 
        by modifying the default branch.ept value 
        # INFO: we make use of order queryset [orders_qs] instead of [get] an instance
            # because i allow to efficiently and dynamicaly update an instance
        TODO: for the mean time branch can only change the quatity of an orderitem or remove it from the order
        later we can maybe give the branch ability to replace an orderitem with a new one
        '''
        try:
            _branch = request.user.branch
            if not _branch:
                return Response(status=status.HTTP_404_NOT_FOUND)

            with transaction.atomic():
                # Get and Lock the row here
                order: Order = Order.objects.select_for_update().get(id=kwargs['orderID'])

                # INFO:: Validation checks
                if order.terminated:
                    raise ValueError("Order already terminated")
                elif order.status != Order.Status.accepted:
                    raise ValueError("Only accepted orders can be marked as ready")

                order.status = Order.Status.ready
                order.ready_at = timezone.now()
                order.save(update_fields=['status', 'ready_at'])

            # INFO:: Courier dispatch
            if order.courier is None:
                publisher.publish(CourierDispatcher.start, _branch.city.id)
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, (Exception, ObjectDoesNotExist, AssertionError)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
