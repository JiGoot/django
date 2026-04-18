# from django.core.exceptions import ObjectDoesNotExist
# from common.authentication import BranchManagerAuth
# from kitchen.models import KitchenTransaction, KitchenProfile, KitchenWallet
# from core.permission import BranchAppAuth
# from kitchen.serializers.transaction import KitchenTransSrz
# from kitchen.serializers.wallet import KitchenWalletSrz
# from core.utils import Currency, formattedError, getDeviceUtcOffset
# from django.core.paginator import Paginator
# from rest_framework import permissions, status
# from rest_framework.response import Response
# from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
# from rest_framework.views import APIView
# import logging


# # Create a logger for this file
# logger = logging.getLogger(__name__)


# class Store__WalletView(APIView):
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
#             _pageId = int(request.query_params.get('page', 1))
#             page_size = int(request.query_params.get('page_size', 15))
#             kitchen: KitchenProfile = request.user.kitchen
#             wallet, created = KitchenWallet.objects.get_or_create(kitchen=kitchen)
#             tranzs = KitchenTransaction.objects.select_related('order').filter(wallet=wallet)
#             paginator = Paginator(tranzs, page_size)
#             if _pageId:
#                 if paginator.num_pages >= int(_pageId):
#                     tranzs = paginator.page(_pageId).object_list
#                 else:  # NOTE No more page
#                     tranzs = KitchenTransaction.objects.none()

#             data = {
#                 'pagination':{
#                     'count': paginator.count,
#                     "has_next": _pageId < paginator.num_pages,
#                 },
               
#                 'wallet': KitchenWalletSrz.default(wallet),
#                 'currency': kitchen.currency,  # INFO:: requested
#                 # 'payout_methods': KitchenPayoutMethodSrz.default(wallet.payout_methods.all()),
#                 'transactions': KitchenTransSrz.default(tranzs),
#                 'utc_diff': utcDiff,
#             }
#             return Response(data, status=status.HTTP_200_OK)

#         except Exception as e:
#             logger.exception(formattedError(e))
#             if isinstance(e, ObjectDoesNotExist | AssertionError | ValueError):
#                 return Response(formattedError(e), status=status.HTTP_400_BAD_REQUEST)
#             return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
