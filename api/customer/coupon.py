

import logging
from rest_framework import generics
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.utils import formattedError

logger = logging.getLogger(name=__file__)


# class Customer__ValidateCouponView(generics.GenericAPIView):
#     authentication_classes = [JWTAuthentication,]
#     permission_classes = [permissions.IsAuthenticated,]
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]

#     def get(self, request, *args, **kwargs):
#         try:
#             code = request.data.get("code")
#             subtotal = float(request.data.get("subtotal", 0))
#             delivery_fee = float(request.data.get("delivery_fee", 0))
#             user: Customer = request.user  # Get authenticated user
#             # --------------------
#             # Coupon View validations
#             assert code, "Coupon code is required."
#             # coupon: KitchenCoupon = KitchenCoupon.objects.get(code=code)
#             assert coupon.is_valid(), "This coupon is expired or has reached its usage limit."
#             # Check if minimum subtotal condition is met
#             if coupon.min_subtotal:
#                 assert subtotal >= coupon.min_subtotal, f"Requires a minimum subtotal of {coupon.min_subtotal}."
#             # Check if user has already used this coupon in a past order
#             if coupon.single_use:
#                 user_coupon_orders = KitchenOrder.objects.filter(
#                     customer=user,
#                     coupon_code=code
#                 ).filter(
#                     Q(placed_at__gte=coupon.valid_from) &
#                     (Q(valid_to__isnull=True) | Q(placed_at__lte=coupon.valid_to))
#                 )
#                 assert user_coupon_orders.exists(), "You have already used this coupon."
#             # ------------------
#             discount = coupon.calculate_discount(subtotal, delivery_fee)
#             return Response(discount, status=status.HTTP_200_OK)
#         except Exception as e:
#             logger.exception(formattedError(e))
#             if isinstance(e, AssertionError) or isinstance(e, ObjectDoesNotExist):
#                 return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
#             return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
