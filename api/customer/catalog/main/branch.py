# """[⎷][⎷][⎷]
# * paginaton: YES
# [_published] - allow to send to the customer user, only data of published kitchens.
# thiis should be done everywhere kitchen data is send to the customer
# [_tags] - allow to fecth kitchen according to user preferences
# """

# # from django.contrib.gis.geos import Point
# # from django.db.models.functions import Distance
# from django.utils.text import slugify  # You can use python-slugify
# import json
# import hashlib
# from django.core.cache import cache
# import pytz
# from rest_framework.throttling import AnonRateThrottle, UserRateThrottle, ScopedRateThrottle
# import logging

# from rest_framework import permissions, status
# from api.customer.apiview import CustomerAPIView
# from branch.models.branch import Branch
# from branch.serializers.branch import BranchSrz
# from common.models.boundary.city import H3_BRANCH_RES, City
# from core.utils import formattedError
# from django.core.exceptions import ObjectDoesNotExist
# from rest_framework.response import Response
# from rest_framework_simplejwt.authentication import JWTAuthentication


# # Create a logger for this file
# logger = logging.getLogger(__name__)
# import pytz, h3


# class Customer__NearbyBranches(CustomerAPIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]
#     throttle_classes = [AnonRateThrottle, UserRateThrottle]

#     def get(self, request, *args, **kwargs):
#         try:
#             # --- PARAMS ---
#             _city_id = request.query_params.get("city_id", 1)  # Default to kinshasa
#             _lat = request.query_params.get("lat", None)
#             _lng = request.query_params.get("lng", None)
#             _typeId = kwargs.get("type_id", None)

#             city: City = City.objects.prefetch_related("branch_types", "service_types").get(id=_city_id)
#             if not _lat or not _lng:
#                 _lat, _lng = city.lat, city.lng

#             city.cached.nearest_branches


#             # cache.set(cached_key, payload, timeout=5 * 60)  # or None for permanent
#             # cache.client.get_client().sadd(branch.cache_key_set, cached_key)
#             return Response(
#                 "",
#                 status=status.HTTP_200_OK,
#             )

#         except Exception as e:
#             logger.exception(formattedError(e))
#             if isinstance(e, (ValueError, ObjectDoesNotExist)):
#                 return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
#             return Response(formattedError(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
