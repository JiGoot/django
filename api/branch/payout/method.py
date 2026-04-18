# from django.core.exceptions import ObjectDoesNotExist, ValidationError
# from rest_framework import permissions, status
# from rest_framework.response import Response
# from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
# from rest_framework.views import APIView
# from common.models import Gateway
# from common.authentication import BranchManagerAuth
# from kitchen.models import FoodBusiness, KitchenPayoutMethod, KitchenWallet
# from kitchen.serializers.payout_method import KitchenPayoutMethodSrz
# from common.serializers import GatewaySrz
# from core.permission import BranchAppAuth

# from core.utils import formattedError, getDeviceUtcOffset
# from django.db import transaction
# import logging

# logger = logging.getLogger(name=__file__)


# class Kitchen__GetPayoutMethods(APIView):
#     authentication_classes = [BranchAppAuth, BranchManagerAuth,]
#     permission_classes = [permissions.IsAuthenticated,]
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]

#     def get(self, request, *args, **kwargs):
#         '''
#         The kitchen balance is based on not yet collected or withdrawn payment transactions minus 
#         not yet collected refund transactions.'''
#         utcDiff = getDeviceUtcOffset(request)

#         try:

#             # TODO:: enable filtering
#             kitchen: FoodBusiness = request.user.kitchen 
#             methods = KitchenPayoutMethod.objects.select_related(
#                 'provider').filter(wallet=kitchen.wallet, provider__is_active=True)
#             return Response(KitchenPayoutMethodSrz.default(methods), status=status.HTTP_200_OK)

#         except Exception as e:
#             logger.exception(formattedError(e))
#             if isinstance(e, AssertionError) or isinstance(e, ObjectDoesNotExist):
#                 return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
#             return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # class Kitchen__AddPayoutMethod(APIView):
# #     '''
# #     FoodBusiness manager can only accept its own order, and is allowed to add [delay] as well as to
# #     add items or remove from t
# #     '''
# #     authentication_classes = [BranchManagerAuth, ]
# #     permission_classes = [permissions.IsAuthenticated,]
# #     throttle_classes = [AnonRateThrottle, UserRateThrottle]

# #     def post(self, request, *args, **kwargs):
# #         try:
# #             raw_pwd = request.data.pop('password', None)
# #             assert raw_pwd, "Missing validation PIN"
# #             kitchen: FoodBusiness = FoodBusiness.objects.select_related(
# #                 'city__country').get(manager=request.user)
# #             wallet, created = KitchenWallet.objects.prefetch_related(
# #                 'methods').get_or_create(kitchen=kitchen)
# #             assert wallet.methods.count() < 2, "No more than two Payout methods is allowed."
# #             with transaction.atomic():
# #                 method = wallet.methods.create(**request.data)
# #                 data = KitchenPayoutMethodSrz.default(method)
# #                 assert check_password(raw_pwd, kitchen.manger.password), "Incorrect Validation PIN"
# #             return Response(data, status=status.HTTP_200_OK)
# #         except Exception as e:
# #             logger.exception(formattedError(e))
# #             if isinstance(e, ObjectDoesNotExist | AssertionError):
# #                 return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
# #             return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # class Kitchen__DeletePayoutMethod(APIView):
# #     '''
# #     FoodBusiness manager can only accept its own order, and is allowed to add [delay] as well as to
# #     add items or remove from t
# #     '''
# #     authentication_classes = [BranchManagerAuth, ]
# #     permission_classes = [permissions.IsAuthenticated,]
# #     throttle_classes = [AnonRateThrottle, UserRateThrottle]

# #     def delete(self, request, *args, **kwargs):
# #         try:
# #             raw_pin = request.data.pop('pin', None)
# #             assert raw_pin, "Missing validation PIN"
# #             kitchen: FoodBusiness = FoodBusiness.objects.select_related('city__country')\
# #                 .get(manager=request.user)
# #             assert isinstance(kitchen, FoodBusiness)
# #             wallet: KitchenWallet = KitchenWallet.objects.prefetch_related('methods')\
# #                 .get(kitchen=kitchen)
# #             assert isinstance(wallet, KitchenWallet)
# #             method: KitchenPayoutMethod = wallet.methods.get(id=kwargs['methodID'])
# #             method.delete()
# #             return Response(status=status.HTTP_200_OK)
# #         except Exception as e:
# #             logger.exception(formattedError(e))
# #             if isinstance(e, AssertionError) or isinstance(e, ObjectDoesNotExist):
# #                 return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
# #             return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
