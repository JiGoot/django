# from django.core.exceptions import ObjectDoesNotExist, ValidationError
# from rest_framework import permissions, status
# from rest_framework.response import Response
# from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
# from rest_framework.views import APIView
# from common.base.payout import BasePayout
# from common.models import Gateway
# from common.authentication import BranchManagerAuth
# from kitchen.models import KitchenPayout, FoodBusiness, BranchManager, KitchenPayoutMethod, KitchenWallet
# from kitchen.serializers.payout import KitchenPayoutSrz
# from core.permission import BranchAppAuth
# from kitchen.serializers.payout_method import KitchenPayoutMethodSrz
# from common.serializers import GatewaySrz
# from core.utils import formattedError, getDeviceUtcOffset
# from django.db import OperationalError, transaction
# import logging

# logger = logging.getLogger(name=__file__)


# class Kitchen__GetPayoutMethods(APIView):
#     authentication_classes = [BranchAppAuth, BranchManagerAuth,]
#     permission_classes = [permissions.BasePermission,]
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]

#     def get(self, request, *args, **kwargs):
#         '''
#         The kitchen balance is based on not yet collected or withdrawn payment transactions minus 
#         not yet collected refund transactions.'''
#         utcDiff = getDeviceUtcOffset(request)

#         try:

#             # TODO:: enable filtering
#             kitchen: FoodBusiness = FoodBusiness.objects.select_related(
#                 'city', 'city__country').get(manager=request.user)
#             methods = KitchenPayoutMethod.objects.select_related(
#                 'provider').filter(wallet=kitchen.wallet, provider__is_active=True)
#             if not methods:
#                 raise ValidationError("Aucune methode de payement associer")
#             data = KitchenPayoutMethodSrz.default(methods),
#             return Response(data, status=status.HTTP_200_OK)

#         except Exception as e:
#             logger.exception(formattedError(e))
#             if isinstance(e, (AssertionError, ValidationError, ObjectDoesNotExist)):
#                 return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
#             return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class Kitchen__AddPayoutRequest(APIView):
#     '''
#     FoodBusiness manager can only accept its own order, and is allowed to add [delay] as well as to
#     add items or remove from t
#     '''
#     authentication_classes = [BranchAppAuth, BranchManagerAuth,]
#     permission_classes = [permissions.IsAuthenticated,]
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]

#     def post(self, request, *args, **kwargs):
#         try:
#             # INFO:: Get and remove [pin] from the request payload
#             raw_pwd = request.data.pop('password', None)
#             assert raw_pwd, "Wrong validation password"
#             manager: BranchManager = request.user
#             kitchen: FoodBusiness = FoodBusiness.objects.select_related('city',
#                                                               'city__country').get(manager=request.user)
#             kitchen.manager.check_password(raw_pwd)
#             with transaction.atomic():
#                 # Lock the wallet row to prevent concurrent modifications
#                 wallet, created = KitchenWallet.objects.select_for_update(
#                     nowait=True).prefetch_related('payouts').get_or_create(kitchen=kitchen)
#                 # Check for ongoing payouts
#                 ongoing = wallet.payouts.filter(
#                     status__in=[BasePayout.Status.pending, BasePayout.Status.approved])
#                 assert not ongoing.exists(), "You currently have an ongoing payout request"
#                 # Get the payout details from the request
#                 _provider = request.data.get('provider')
#                 _amount = request.data.get('amount')
#                 assert _amount <= wallet.balance, "Insufficient wallet balance"
#                 pp: Gateway = Gateway.objects.filter(
#                     country=kitchen.city.country, is_active=True).get(name=_provider)
#                 assert _amount >= pp.min, f"Minimum amount limit is {pp.min}"
#                 assert _amount <= pp.max, f"Maximum amount limit is {pp.max}"
#                 # INFO:: Check if the provider is valid
#                 _providers = vars(BasePayout.Providers).values()
#                 assert _provider in _providers, f"{_provider} not a supported provider"
#                 # Create the payout
#                 payout = wallet.payouts.create(
#                     manager_name=manager.name,
#                     manager_last_name=manager.last_name,
#                     ** request.data)
#                 data = KitchenPayoutSrz.default(payout)
#                 # TODO:: remove it later when kitchen will be able to reset the kitchen pin from the app
#                 # send the OTP code for resenting pin to the kitchen manager phone number.

#             return Response(data, status=status.HTTP_200_OK)
#         except Exception as e:
#             logger.exception(formattedError(e))
#             if isinstance(e, AssertionError) or isinstance(e, ObjectDoesNotExist):
#                 return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
#             elif isinstance(e, OperationalError):
#                 return Response("Wallet is already locked by another transaction, Please try again later", status=status.HTTP_400_BAD_REQUEST)
#             return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class Kitchen__DeletePayoutRequest(APIView):
#     '''
#     FoodBusiness manager can only accept its own order, and is allowed to add [delay] as well as to
#     add items or remove from t
#     '''
#     authentication_classes = [BranchManagerAuth, ]
#     permission_classes = [permissions.IsAuthenticated,]
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]

#     def delete(self, request, *args, **kwargs):
#         '''# INFO: we make use of order queryset [orders_qs] instead of [get] an instance
#             # because i allow to efficiently and dynamicaly update an instance
#         TODO: for the mean time kitchen can only change the quatity of an orderitem or remove it from the order
#         later we can maybe give the kitchen ability to replace an orderitem with a new one
#         '''
#         try:
#             # INFO:: Get and remove [pin] from the request payload
#             raw_pwd = request.data.pop('password', None)
#             assert raw_pwd, "Missing validation PIN"
#             kitchen: FoodBusiness = FoodBusiness.objects.get(manager=request.user)
#             kitchen.manager.check_password(raw_pwd)
#             wallet: KitchenWallet = KitchenWallet.objects.prefetch_related(
#                 'payouts').get(kitchen=kitchen)
#             payout: KitchenPayout = wallet.payouts.get(id=kwargs['PayoutID'])
#             assert payout.status == BasePayout.Status.pending, "Only PENDING payout can be deleted"
#             payout.delete()
#             return Response(status=status.HTTP_200_OK)
#         except Exception as e:
#             logger.exception(formattedError(e))
#             if isinstance(e, AssertionError) or isinstance(e, ObjectDoesNotExist):
#                 return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
#             return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
