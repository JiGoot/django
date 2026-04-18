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
from affiche.models import Affiche
from affiche.serializers import AfficheSrz
from api.customer.cached.store_catalog import CachedStoreCatalog
from api.customer.apiview import CustomerAPIView
from branch.models.branch import Branch
from branch.models.shift import Shift
from branch.models.variant import BranchVariant
from branch.serializers.branch import BranchSrz
from common.models import City, Zone
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


# class CatalogAdsAnonThrottle(AnonRateThrottle):
#     rate = "5/min"


# class CatalogAdsUserThrottle(UserRateThrottle):
#     rate = "10/min"


class Customer__CarouselAds(CustomerAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    class AnonThrottle(AnonRateThrottle):
        rate = "5/min"

    class UserThrottle(UserRateThrottle):
        rate = "10/min"

    def get_throttles(self):
        if self.request.user.is_authenticated:
            return [self.UserThrottle()]
        return [self.AnonThrottle()]

    class Cached:
        @classmethod
        def city_ads(cls, city_id):
            return f"city_ads::{city_id}"

    def get(self, request, *args, **kwargs):

        try:
            # --- PARAMS ---
            _city_id = request.query_params.get("city_id", 1)  # Default to kinshasa

            """Handle cache"""
            cached_key = self.Cached.city_ads(_city_id)
            cached = cache.get(cached_key)
            try:
                if cached:
                    return Response(cached, status=status.HTTP_200_OK)
            except Exception as e:
                logger.warning(formattedError(e))

            """Compute Logic"""

            payload = AfficheSrz.Customer(
                Affiche.objects.filter(city_id=_city_id), many=True, context={"request": request}
            ).data
            cache.set(cached_key, payload, timeout=5 * 60)  # or None for permanent
            return Response(payload, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(formattedError(e))
            if isinstance(e, (ValueError, ObjectDoesNotExist)):
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
            return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
