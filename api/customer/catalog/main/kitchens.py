"""[⎷][⎷][⎷]
* paginaton: YES
[_published] - allow to send to the customer user, only data of published kitchens.
thiis should be done everywhere kitchen data is send to the customer
[_tags] - allow to fecth kitchen according to user preferences
"""

from datetime import datetime
import math
import time
from typing import Optional

# from django.contrib.gis.geos import Point
# from django.db.models.functions import Distance
from django.utils.text import slugify  # You can use python-slugify
import json
import hashlib
from django.core.cache import cache
import pytz
from rest_framework.throttling import (
    AnonRateThrottle,
    UserRateThrottle,
    ScopedRateThrottle,
)
import logging

from rest_framework import permissions, status
from api.customer.apiview import CustomerAPIView
from branch.models.branch import Branch
from branch.serializers.branch import BranchSrz
from common.models.boundary.city import H3_BRANCH_RES, City
from core.utils import formattedError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.db.models import Case, Count, Q, Value, When, Prefetch
from django.db.models import Case, When, Value, BooleanField
from django.db.models import Exists, OuterRef, Window, F


from django.utils import timezone
import pytz, h3
from django.db.models import F, FloatField
from django.db.models.functions import Radians, Sin, Cos, ACos
from django.db.models import F, Value, ExpressionWrapper, IntegerField
from django.db.models.expressions import Func
from django.db.models.functions import ACos, Cos, Sin, Radians, Least, Greatest
from django.db.models.query import QuerySet
from django.db.models.functions import RowNumber
from django.core.paginator import Page, Paginator, EmptyPage, PageNotAnInteger

# Create a logger for this file
logger = logging.getLogger(__name__)


from django.db.models import F, FloatField, IntegerField
from django.db.models.functions import ACos, Cos, Radians, Sin, Floor


def get_radial_rings(center_lat, center_lng, ring_width_km=1.0):
    # Standard Haversine constant (Earth's radius in km)
    R = 6371.0

    # 1. Calculate precise distance (km)
    # 2. Divide by ring_width_km (e.g., 1.5km per ring)
    # 3. Floor the result to get 0, 1, 2, 3...

    distance_expr = R * ACos(
        Cos(Radians(center_lat)) * Cos(Radians(F("lat"))) * Cos(Radians(F("lng")) - Radians(center_lng))
        + Sin(Radians(center_lat)) * Sin(Radians(F("lat")))
    )

    return Branch.objects.annotate(
        precise_dist=distance_expr,
        ring_level=Floor(F("precise_dist") / ring_width_km, output_field=IntegerField()),
    ).order_by("ring_level", "precise_dist")


class Customer__GetNearbyBranches(CustomerAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # throttle_classes = [AnonRateThrottle, UserRateThrottle]

    class Cached:
        @classmethod
        def nearest_catalog(cls, h3_cell):
            return f"nearest_kitchens::{h3_cell}"

    def get(self, request, *args, **kwargs):

        try:
            # --- PARAMS ---
            _cityId = request.query_params.get("city_id", 1)
            _lat = request.query_params.get("lat", None)
            _lng = request.query_params.get("lng", None)
            _tags = request.query_params.get("tags", None)
            _typeId = kwargs.get("type", None)
            """Compute Logic"""
            city: City = City.objects.get(id=_cityId)
            if not _lat or not _lng:
                _lat, _lng = city.lat, city.lng

            

            # If not cached, fetch from the database
            page = city.cached.nearest_branches(_typeId,_lat, _lng,  tags=_tags)
            payload = BranchSrz.Customer.default(page)
            return Response(payload, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, (ValueError, ObjectDoesNotExist)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
