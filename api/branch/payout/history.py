# from django.core.exceptions import ObjectDoesNotExist
# from common.authentication import BranchManagerAuth
# from kitchen.models import KitchenPayout, FoodBusiness, KitchenWallet
# from kitchen.serializers.payout import KitchenPayoutSrz
# from core.permission import BranchAppAuth
# from django.core.paginator import Paginator
# from rest_framework import permissions, status
# from rest_framework.response import Response
# from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
# from rest_framework.views import APIView
# import logging


# # Create a logger for this file
# logger = logging.getLogger(__name__)


# class Kitchen__PayoutHistory(APIView):
#     authentication_classes = [BranchAppAuth, BranchManagerAuth,]
#     permission_classes = [permissions.BasePermission,]
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]

#     def get(self, request, *args, **kwargs):
#         '''
#         The kitchen balance is based on not yet collected or withdrawn payment transactions minus 
#         not yet collected refund transactions.'''
#         utcDiff = getDeviceUtcOffset(request)

#         try:
#             _pageId = int(request.query_params.get('page', 1))
#             page_size = int(request.query_params.get('page_size', 15))
#             # TODO:: enable filtering
#             kitchen:FoodBusiness = FoodBusiness.objects.select_related('city__country').get(manager=request.user)
#             wallet, created = KitchenWallet.objects.prefetch_related(
#                 'methods').get_or_create(kitchen=kitchen)
#             payouts = KitchenPayout.objects.filter(wallet=wallet)
#             paginator = Paginator(payouts, page_size)
#             if _pageId:
#                 if paginator.num_pages >= int(_pageId):
#                     payouts = paginator.page(_pageId).object_list
#                 else:  # NOTE No more page
#                     payouts = KitchenPayout.objects.none()
#             data = {
#                 "has_next": _pageId < paginator.num_pages,
#                 'payouts': KitchenPayoutSrz.default(payouts),
#                 'utc_diff': utcDiff,
#             }
#             return Response(data, status=status.HTTP_200_OK)

#         except Exception as e:
#             logger.exception(formattedError(e))
#             if isinstance(e, AssertionError) or isinstance(e, ObjectDoesNotExist):
#                 return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
#             return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
