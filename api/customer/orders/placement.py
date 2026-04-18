from api.customer.apiview import CustomerAPIView
from branch.models.branch import Branch
from branch.models.variant import BranchVariant, BranchVariantDailySales
from branch.models.manager import BranchManager
from customer.models.customer import Customer
from order.models import Order, OrderItem
from customer.models.payment import Payment
from core.rabbitmq.broker import publisher
from django.db.models.functions import Coalesce
from decimal import Decimal

# from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from core.tasks.fcm import FCM_Notify
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from core.utils import formattedError
from django.db import transaction
from django.db import models
import logging


logger = logging.getLogger(name=__file__)
from typing import Optional, Union


class Customer__PlacingStoreOrder(CustomerAPIView):
    """NOTE [⎷]
    - create order
    - subscribe user and skitchen to FCM channels of [#<order.pk>]  (may be optional we can simply send data directly via token)
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request, **kwargs):
        # LNG_CODE = request.META.get('HTTP_LANGUAGE_CODE', 'en')
        items_data = request.data.pop("items", [])
        _paymentData = request.data.pop("payment", None)
        should_log = True
        # _city_id = request.data.pop("city_id")
        _branch_id = request.data.pop("branch_id", None)

        try:
            # STEP 1: Validations
            if not _branch_id:
                raise ValueError("A branch is requires.")
            lat = float(request.data.pop("dropoff_lat", 0))
            lng = float(request.data.pop("dropoff_lng", 0))
            if not lat or not lng:
                raise ValueError("Drop-off Lat and Lng data are required.")
            customer:Customer = request.user
            with transaction.atomic():

                branch: Branch = Branch.objects.select_related(
                    "manager",
                    "supplier",
                    "supplier__commission",
                ).get(id=_branch_id)
                if not branch:
                    raise ValueError("Missing the associated branch.")

                # TODO:: Check if the branch has the selected delivery type among its active delivery types, if not raise an error


                # INFO :: if POP, Make sure that an order payment hav been maid
                # if _paymentData:
                #     if _paymentData['method'] != Payment.Methods.cash:
                #         if _paymentData['amount'] and _paymentData['transaction_id']:
                #             # TODO:: Get from [request.data] the payment transaction_id
                #             # TODO:: Use the payment transaction_id  to check from the provider the satstus of the transaction,
                #             # TODO:: if payment transaction status from the third party provider is paid, create a Jigoot based equivalent
                #             # from Payment instance with the amount paid, maybe have a separete Payement model (order)
                #             # NOTE transaction instance are created only when the order is completed
                #             #  i send an sync request to check if the payment transaction was sa
                #             pass
                #             return Response(status=status.HTTP_402_PAYMENT_REQUIRED)

                # STEP 2: Check for ongoing unpaid orders
                payments = (
                    Payment.objects.filter(order=models.OuterRef("pk"))
                    .values("order")
                    .annotate(total=models.Sum("amount"))
                    .values("total")
                )

                has_unpaid_orders = (
                    Order.objects.filter(customer=request.user)
                    .exclude(status__in=[Order.Status.cancelled, Order.Status.delivered])
                    .annotate(
                        total_amount=models.F("subtotal")
                        + models.F("small_order_fee")
                        + models.F("delivery_fee"),
                        paid_amount=Coalesce(models.Subquery(payments), Decimal("0.00")),
                    )
                    .filter(total_amount__gt=models.F("paid_amount"))
                    .exists()
                )
                if has_unpaid_orders:
                    should_log = False
                    raise AssertionError(
                        "Vous avez commande en cours non payée. Veuillez la finaliser avant de passer une nouvelle commande."
                    )

                # STEP 3: Create order
                _order: Order = Order.objects.create(
                    customer=request.user,
                    branch=branch,
                    ept=branch.ept,
                    dropoff_lat=lat,
                    dropoff_lng=lng,
                    currency=branch.currency,
                    commission_type=branch.supplier.commission.type,
                    commission_value=branch.supplier.commission.value,
                    **request.data,
                )

                

                # STEP 4: Lock variants to prevent race conditions

                # variant_ids = [obj["variant_id"] for obj in items_data]
                # locked_variants = BranchVariant.objects.filter(
                #     id__in=variant_ids,
                #     branch=branch,         # make sure it's the correct branch
                #     is_available=True      # optional
                # ).select_for_update(of=("self",))

                # variant_map = {v.id: v for v in locked_variants}

                # missing = set(variant_ids) - set(variant_map.keys())
                # if missing:
                #     raise ValueError(f"Variants not found or unavailable: {missing}")

                # STEP 5: Create order items & allocate stock via StockMovement

                for obj in items_data:  # NOTE :: Create order's items instances.

                    # Create OrderItem
                    OrderItem.objects.create(order=_order,**obj)


            # Notify
            manager: BranchManager = branch.manager
            if manager:
                publisher.publish(
                    FCM_Notify.Branch.incoming,
                    manager.token.fcm,
                    _order.code,
                    _order.placed_at.isoformat(),
                )

            # TODO #NextVersion  on order placed schedule a task in 10 minutes
            # to verify if the order has been accepted, cancel if not with a [timeout] type
            return Response(status=status.HTTP_200_OK)

        except Exception as e:
            if should_log:
                logger.exception(formattedError(e))
            if isinstance(e, AssertionError) or isinstance(e, ObjectDoesNotExist):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
