
from api.customer.apiview import CustomerAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.paginator import Paginator, Page, EmptyPage, PageNotAnInteger
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from core.utils import formattedError
import logging
from django.db.models import Case, When, F, Value, IntegerField, DurationField
from django.db.models.functions import Now, Coalesce
from customer.models.customer import Customer
from order.models.order import Order
from order.serializers.order import OrderSrz
from django.db.models.functions import Greatest

logger = logging.getLogger(name=__file__)


class Customer__Orders(CustomerAPIView):
    """[⎷][⎷][⎷]
    - query param:
        - page -- for pagination
        - per_page -- for page content size in pagination
        - status -- filetr only user orders corresponding to the given status

    * Retrieve all [orders placed] by a [user] or all [orders placed] by [user] and
    by [status].
    * permission_classes:   -  Authorized user
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, *args, **kwargs):
        try:
            _pageId = int(request.query_params.get("page", 1))
            _page_size = int(request.query_params.get("page_size", 15))
            _status = request.query_params.get("status", None)
            _customer: Customer = request.user
            _orders = (
                Order.objects.prefetch_related("payments")
                .select_related("branch")
                .filter(customer=_customer)
                .annotate(
                    # item_count=Count("items"), # TODO:: use a item_count field similar to wallet.balance or storevariant.stock
                    time_in_status=Case(
                        When(status="placed", then=Now() - F("placed_at")),
                        When(
                            status="accepted",
                            then=Now() - Coalesce(F("accepted_at"), F("placed_at")),
                        ),
                        When(
                            status="ready",
                            then=Now() - Coalesce(F("ready_at"), F("placed_at")),
                        ),
                        output_field=DurationField(),
                    ),
                    updated_at=Greatest(
                        "placed_at",
                        "accepted_at",
                        "ready_at",
                        "pickedup_at",
                        "delivered_at",
                        "cancelled_at",
                    ),
                )
                .order_by("-placed_at")
            )

            if _status != None:
                _orders = _orders.filter(status=_status)
            # NOTE ----- Pagination -----
            paginator = Paginator(_orders, _page_size)
            try:
                page = paginator.page(_pageId)
            except (EmptyPage, PageNotAnInteger):
                # make an empty page with the requested page number
                page = Page([], _pageId, paginator)

            # NOTE ----- Response -----
            data = {
                "pagination": {
                    "count": paginator.count,
                    "total_pages": paginator.num_pages,
                    "current_page": page.number,
                    "has_next": page.has_next(),
                },
                "results": OrderSrz.Customer.basic(page),
            }
            return Response(data, status=status.HTTP_200_OK)
        except (ValueError, Order.DoesNotExist) as e:
            logger.warning(formattedError(e))
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(formattedError(e))
            return Response(
                formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
