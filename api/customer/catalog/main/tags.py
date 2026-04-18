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
from api.customer.cached.store_catalog import CachedStoreCatalog
from api.customer.apiview import CustomerAPIView
from branch.models.branch import Branch
from branch.models.shift import Shift
from branch.models.tag import Tag
from branch.models.variant import BranchVariant
from branch.serializers.branch import BranchSrz
from branch.serializers.tag import TagSrz
from common.models import City, Zone
from common.models.boundary.city import H3_BRANCH_RES
from common.models.catalog.category import Category
from common.models.catalog.section import Section, SectionCategory
from core import settings
from core.utils import formattedError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.db.models import Case, Count, Q, Value, When, Prefetch
from django.db.models import Case, When, Value, BooleanField
from django.db.models import Exists, OuterRef, Window, F

# Create a logger for this file
logger = logging.getLogger(__name__)
from django.utils import timezone
import pytz, h3
from django.db.models import F, FloatField
from django.db.models.functions import Radians, Sin, Cos, ACos
from django.db.models import F, Value, ExpressionWrapper, IntegerField
from django.db.models.expressions import Func
from django.db.models.functions import ACos, Cos, Sin, Radians, Least, Greatest
from django.db.models.query import QuerySet
from django.db.models.functions import RowNumber
from django.core.paginator import Paginator


class Customer__BranchTypeTags(CustomerAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    class Cached:
        @classmethod
        def tags(cls, city_id):
            return f"city::{city_id}::tags"

    def get(self, request, *args, **kwargs):

        try:
            _branchTypeId = request.query_params.get("branch_type_id", None)
            _cityId = request.query_params.get("city_id", 1)
            _lat = request.query_params.get("lat", None)
            _lng = request.query_params.get("lng", None)

            city: City = City.objects.get(id=_cityId)
            if not _lat or not _lng:
                _lat, _lng = city.lat, city.lng

            # Get the target H3 cell
            target_cell = h3.latlng_to_cell(float(_lat), float(_lng), H3_BRANCH_RES)
            # Get customer default service grid for the given city.

            tags = (
                Tag.objects.select_related("type")
                .filter(
                    is_active=True,
                    type__is_active=True,
                    # NOTE :: If we want only tags with existing active branches to be returned 
                    # suppliers__branches__type_id=_typeId,
                    # suppliers__branches__city_id=_cityId,
                    # suppliers__branches__is_active=True,
                    # ← limit to k-ring
                    # suppliers__branches__h3_res8__in=h3.grid_disk(target_cell, city.k_ring),
                )
            )
            if _branchTypeId:
                tags = tags.filter(type_id=int(_branchTypeId))
            tags = tags .distinct().order_by("index")
            # TODO:: Later add popularity score and order by it
            # the popularity_score can be computed once every week.
            return Response(TagSrz.default(tags), status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, (ValueError, ObjectDoesNotExist)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
