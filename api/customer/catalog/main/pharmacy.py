# """[⎷][⎷][⎷]
# * paginaton: YES
# [_published] - allow to send to the customer user, only data of published kitchens.
# thiis should be done everywhere kitchen data is send to the customer
# [_tags] - allow to fecth kitchen according to user preferences
# """

# from datetime import datetime
# import math
# import time
# from typing import Optional

# # from django.contrib.gis.geos import Point
# # from django.db.models.functions import Distance
# from django.utils.text import slugify  # You can use python-slugify
# import json
# import hashlib
# from django.core.cache import cache
# import pytz
# from rest_framework.throttling import (
#     AnonRateThrottle,
#     UserRateThrottle,
#     ScopedRateThrottle,
# )
# import logging

# from rest_framework import permissions, status
# from affiche.models import Affiche
# from api.customer.cached.store_catalog import CachedStoreCatalog
# from api.customer.apiview import CustomerAPIView
# from branch.models.branch import Branch
# from branch.models.shift import Shift
# from branch.models.variant import BranchVariant
# from branch.serializers.branch import BranchSrz
# from common.models import City, Zone
# from common.models.catalog.category import Category
# from common.models.catalog.section import Section, SectionCategory
# from core import settings
# from core.utils import formattedError
# from django.core.exceptions import ObjectDoesNotExist
# from rest_framework.response import Response
# from rest_framework_simplejwt.authentication import JWTAuthentication

# from django.db.models import Case, Count, Q, Value, When, Prefetch
# from django.db.models import Case, When, Value, BooleanField
# from django.db.models import Exists, OuterRef, Window, F

# # Create a logger for this file
# logger = logging.getLogger(__name__)
# from django.utils import timezone
# import pytz, h3
# from django.db.models import F, FloatField
# from django.db.models.functions import Radians, Sin, Cos, ACos
# from django.db.models import F, Value, ExpressionWrapper, IntegerField
# from django.db.models.expressions import Func
# from django.db.models.functions import ACos, Cos, Sin, Radians, Least, Greatest
# from django.db.models.query import QuerySet
# from django.db.models.functions import RowNumber
# from django.core.paginator import Paginator


# class Customer__Nearby_Pharmacy(CustomerAPIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]

#     class Cached:
#         @classmethod
#         def nearest_catalog(cls, h3_cell):
#             return f"nearest_store_catalog::{h3_cell}"

#     def get(self, request, *args, **kwargs):

#         try:
#             # --- PARAMS ---
#             _city_id = request.query_params.get("city_id", 1)  # Default to kinshasa
#             # _zone_id = request.query_params.get("zone_id", None)
#             _lat = request.query_params.get("lat", None)
#             _lng = request.query_params.get("lng", None)

#             cell = (
#                 h3.latlng_to_cell(float(_lat), float(_lng), 9)
#                 if (_lat and _lng)
#                 else _city_id
#             )

#             """Handle cache"""
#             cached_key = self.Cached.nearest_catalog(cell)
#             # cached = cache.get(cached_key)
#             # try:
#             #     if cached:
#             #         cached["cached"] = True
#             #         return Response(cached, status=status.HTTP_200_OK)
#             # except Exception as e:
#             #     logger.warning(formattedError(e))

#             """Compute Logic"""
#             city: City = City.objects.get(id=_city_id)
#             if not _lat or not _lng:
#                 _lat, _lng = city.lat, city.lng
#             # --- GET STORES ---
#             tz = pytz.timezone(city.timezone)  # e.g. "Africa/Kinshasa"
#             local_now = timezone.now().astimezone(tz)
#             active_shifts = Shift.objects.filter(
#                 branch=OuterRef("pk"),  # Correlate with the outer Kitchen query
#                 weekdays__contains=[local_now.isoweekday()],
#                 start__lte=local_now.time(),
#                 end__gte=local_now.time(),
#                 is_active=True,
#             )
#             # Get the first pharmacy
#             pharmacy: Branch = (
#                 Branch.objects.filter(type=BranchType.pharmacy, city=city, is_active=True)
#                 .select_related("supplier")
#                 .annotate(
#                     has_shift=Exists(active_shifts),
#                     is_closed=Case(
#                         When(status=Branch.Status.closed, then=Value(True)),
#                         When(
#                             Q(has_shift=True) & ~Q(status=Branch.Status.closed),
#                             then=Value(False),
#                         ),
#                         default=Value(True),
#                         output_field=BooleanField(),
#                     ),
#                     dist=Func(
#                         Func(F("lng"), F("lat"), function="ST_MakePoint"),
#                         Func(float(_lng), float(_lat), function="ST_MakePoint"),
#                         function="ST_DistanceSphere",
#                         output_field=FloatField(),
#                     ),
#                     ring=Func(
#                         F("dist") / Value(500),
#                         function="FLOOR",
#                         output_field=IntegerField(),
#                     ),
#                 )
#                 .order_by("-is_closed", "ring")
#                 .first()
#             )

#             if not pharmacy:  # Fallback if coordinates missing or no nearby pharmacy found
#                 return Response(
#                     "No active pharmacy found.", status=status.HTTP_204_NO_CONTENT
#                 )
#             payload = BranchSrz.Customer.default(pharmacy)
#             cache.set(cached_key, payload, timeout=5 * 60)  # or None for permanent
#             cache.client.get_client().sadd(pharmacy.cache_key_set, cached_key)
#             return Response(payload, status=status.HTTP_200_OK)

#         except Exception as e:
#             logger.exception(formattedError(e))
#             if isinstance(e, (ValueError, ObjectDoesNotExist)):
#                 return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
#             return Response(
#                 formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
