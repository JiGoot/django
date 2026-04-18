"""[⎷][⎷][⎷]
* paginaton: YES
[_published] - allow to send to the customer user, only data of published kitchens.
thiis should be done everywhere kitchen data is send to the customer
[_tags] - allow to fecth kitchen according to user preferences
"""

# from django.contrib.gis.geos import Point
# from django.db.models.functions import Distance
from django.utils.text import slugify  # You can use python-slugify
from django.core.cache import cache
import pytz
from rest_framework.throttling import (
    AnonRateThrottle,
    UserRateThrottle,
    ScopedRateThrottle,
)
import logging

from rest_framework import permissions, status
from api.customer.cached.store_catalog import CachedStoreCatalog
from api.customer.apiview import CustomerAPIView
from branch.models.branch import Branch
from branch.models.shift import Shift
from branch.models.variant import BranchVariant
from common.models.boundary.city import City
from common.models.catalog.category import Category
from core.utils import formattedError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.db.models import Case, Q, Value, When
from django.db.models import Case, When, Value, BooleanField
from django.db.models import Exists, OuterRef, F
from common.serializers.category import CategorySrz

# Create a logger for this file
logger = logging.getLogger(__name__)
from django.utils import timezone
import pytz, h3
from django.db.models import F, FloatField
from django.db.models import F, Value, IntegerField
from django.db.models.expressions import Func


class Customer__FeatureCats(CustomerAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    class Cached:
        @classmethod
        def featured_cats(cls, h3_cell):
            return f"feature_cats::{h3_cell}"

    def get(self, request, *args, **kwargs):

        try:
            # --- PARAMS ---
            _city_id = request.query_params.get("city_id", 1)  # Default to kinshasa
            _lat = request.query_params.get("lat", None)
            _lng = request.query_params.get("lng", None)

            cell = h3.latlng_to_cell(float(_lat), float(_lng), 9) if (_lat and _lng) else _city_id

            """Handle cache"""
            cached_key = self.Cached.featured_cats(cell)
            cached = cache.get(cached_key)
            try:
                if cached:
                    return Response(cached, status=status.HTTP_200_OK)
            except Exception as e:
                logger.warning(formattedError(e))

            """Compute Logic"""
            city: City = City.objects.get(id=_city_id)
            if not _lat or not _lng:
                _lat, _lng = city.lat, city.lng

            # --- GET STORES ---
            tz = pytz.timezone(city.timezone)  # e.g. "Africa/Kinshasa"
            local_now = timezone.now().astimezone(tz)

            active_shifts = Shift.objects.filter(
                branch=OuterRef("pk"),  # Correlate with the outer Kitchen query
                weekdays__contains=[local_now.isoweekday()],
                start__lte=local_now.time(),
                end__gte=local_now.time(),
                is_active=True,
            )

            branch: Branch = (
                Branch.objects.filter(supplier__isnull=True, city=city)
                .annotate(
                    has_shift=Exists(active_shifts),
                    is_closed=Case(
                        When(status=Branch.Status.closed, then=Value(True)),
                        When(
                            Q(has_shift=True) & ~Q(status=Branch.Status.closed),
                            then=Value(False),
                        ),
                        default=Value(True),
                        output_field=BooleanField(),
                    ),
                    dist=Func(
                        Func(F("lng"), F("lat"), function="ST_MakePoint"),
                        Func(float(_lng), float(_lat), function="ST_MakePoint"),
                        function="ST_DistanceSphere",
                        output_field=FloatField(),
                    ),
                    ring=Func(
                        F("dist") / Value(500),
                        function="FLOOR",
                        output_field=IntegerField(),
                    ),
                )
                .order_by("-is_closed", "ring")
                .first()
            )
            if not branch:  # Fallback if coordinates missing or no nearby branch found
                return Response("No active branch found.", status=status.HTTP_204_NO_CONTENT)

            """
            Return active branch categories grouped by active sections.
            """

            # Branch categories - optimize with exists check

            branch_categories = (
                Category.objects.filter(
                    parent__isnull=True,
                    supplier__isnull=True,  # platform categories only
                    subcategories__category_items__is_active=True,  # ensure it has children with items
                )
                .annotate(
                    has_branch_variants=Exists(
                        BranchVariant.objects.select_related(
                            "supplier_variant", "supplier_variant__variant"
                        ).filter(
                            branch_id=branch.id,
                            supplier_variant__variant__item__category_items__category__parent=OuterRef("pk"),
                            variant__item__category_items__is_active=True,
                        )
                    )
                )
                .filter(has_branch_variants=True)
                .distinct()
            )

            payload = CategorySrz.default(branch_categories)
            cache.set(cached_key, payload, timeout=5 * 60)  # or None for permanent
            # cache.client.get_client().sadd(branch.cache_key_set, cached_key)
            return Response(payload, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, (ValueError, ObjectDoesNotExist)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
