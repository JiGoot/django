from datetime import datetime
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from django.db.models import Case, F, FloatField, Q,   Sum, Value, When
from core.utils import formattedError
from courier.authentication import CourierAuthentication
from django.core.paginator import Paginator
import logging

from courier.models.courier import Courier
from wallet.models.transaction import Transaction
from wallet.serializers.transaction import TransactionSrz


# Create a logger for this file
logger = logging.getLogger(__name__)

class Courier__TransactionsView(APIView):
    authentication_classes = [CourierAuthentication,]
    permission_classes = [permissions.BasePermission,]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        '''
        The kitchen balance is based on not yet collected or withdrawn payment transactions minus 
        not yet collected refund transactions.'''
        courier:Courier = request.user.courier
        try:
            if isinstance(courier, Courier):
                _pageId = int(request.query_params.get('page', 1))
                page_size = int(request.query_params.get('page_size', 15))
                currency = kwargs.get('currency', None)
                start = request.query_params.get('start', None)
                end = request.query_params.get('start', None)
                # TODO last week if start end params are null
                tranzs = Transaction.objects.filter(courier=courier)

                # INFO:: Get transations of a given curriencies
                Currency = tranzs.values('currency').distinct()
                Currency = list(set(entry['currency'] for entry in Currency))

                if not currency:
                    currency = Currency[0]
                tranzs = tranzs.filter(currency=currency)

                # SECTION:: Get all uncollected transactionS
                uncollected = tranzs.filter(collected=False).aggregate(
                    balance=Sum(
                        Case(
                            When(Q(amount__isnull=False), then=F('amount')),
                            default=Value(0),
                            output_field=FloatField(),
                        )
                    ),)
                # INFO:: Get the current kitchen balance
                # A kitchen balance reflects the total earnings and charges for the kitchen that have not yet been included in any payout.
                balance = uncollected['balance']

                # SECTION:: Get TODO filtering by date created
                if start and end:
                    startDate = datetime.strptime()
                    endDate = datetime.strptime()
                    # INFO:: TODO get [tranzs] betwen a start date and end date
                    tranzs = tranzs.filter(
                        date_created__gte=startDate, date_created__lte=endDate,)
                

                # data = tranzs.aggregate(
                #     # INFO::  The sum of all uncollected credit and debit transactions
                #     earnings=Sum(
                #         Case(
                #             When(Q(type=TranzTypes.earning), then=F('amount')),
                #             default=Value(0),
                #             output_field=FloatField(),
                #         )
                #     ),
                #     fees=Sum(
                #         Case(
                #             When(
                #                 ~Q(type=TranzTypes.earning), then=F('amount')),
                #             default=Value(0),
                #             output_field=FloatField(),
                #         )
                #     ),

                # )
                subtotals = data['earnings']
                fees = data['fees']
                paginator = Paginator(tranzs, page_size)
                if _pageId:
                    if paginator.num_pages >= int(_pageId):
                        tranzs = paginator.page(_pageId).object_list
                    else:  # NOTE No more page
                        tranzs = Transaction.objects.none()

                # INFO :: ----- Response -----
                data = {
                    "count": paginator.count,
                    "num_pages": paginator.num_pages,
                    "has_next": _pageId < paginator.num_pages,
                    'balance': balance,
                    'subtotals': subtotals,
                    'fees': fees,
                    'currency': currency,
                    # INFO:: currency's transaction  within kitchen transaction record
                    'Currency': Currency,
                    'results': TransactionSrz.default(tranzs),
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response("Unregistered courier", status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response('Internal error occurred!', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # else:
        #     return Response("Matching kitchen not found", status=status.HTTP_401_UNAUTHORIZED)


# TODO delete only collected transaction alder than 2 months
