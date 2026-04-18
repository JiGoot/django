import logging
from rest_framework.views import APIView
from api.services.travel_metrics import get_travel_metrics
from common.models.app import App, Release
from core.utils import AppType, formattedError, getDeviceUtcOffset
from rest_framework import permissions, status
from rest_framework.response import Response
from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from courier.authentication import CourierAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication


logger = logging.getLogger(name=__file__)

import h3


"""
CODE:

edge_m = h3.average_hexagon_edge_length(res, unit="m")
apothem_m = edge_m * 0.86602540378
flat_to_flat_m = edge_m * 1.73205080757

OUTPUT:

| Res | Edge (m) | Apothem (m) | Flat-to-flat (m) |
| --- | -------- | ----------- | ---------------- |
| 8   | 531      | 460         | 920              |
| 9   | 201      | 174         | 348              |
| 10  | 76       | 66          | 131              |


WHERE:

| Metric                        | Meaning                         |
| ----------------------------- | ------------------------------- |
| **Edge length**               | length of one hex side          |
| **Apothem**                   | center → middle of an edge      |
| **Diameter (flat-to-flat)**   | distance between opposite sides |
| **Diameter (point-to-point)** | corner to corner                |


✅ Recommendation:
Use res-9, flat-to-flat ≈ 350 m, for travel-metrics caching.
Most deliveries in cities like Kinshasa are < 5 km, so ~350 m is precise enough for ETA/fee.
You get good cache hit rate without overloading cache keys.
Optional: use res-10 if you have super short deliveries (<1 km) and need very fine granularity, but res-9 is generally enough.

"""


def get_cache_ttl(distance_m, detour_index=1.0):
    """
    Distance + detour-index-based TTL for travel metrics.

    - distance_m: straight-line or network distance in meters
    - detour_index: network distance / straight-line distance (>= 1)

    Logic:
    - Short trips: smaller TTL
    - Higher DI: shorter TTL (more uncertain routes)
    - Clamp TTL between 2 and 10 minutes
    """
    # Base TTL by distance
    if distance_m < 1000:  # < 1 km
        ttl = 5 * 60  # 5 min
    elif distance_m < 2000:  # 1–2 km
        ttl = 7 * 60  # 7 min
    else:  # 2–3 km
        ttl = 10 * 60  # 10 min

    # Adjust by detour index (higher DI -> shorter TTL)
    # E.g., DI = 1.0 → no change, DI = 1.5 → reduce TTL by ~25%
    factor = 1.0 / detour_index
    ttl = int(ttl * factor)


class TravelMetricsView(APIView):
    authentication_classes = [JWTAuthentication, CourierAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        src = request.query_params.get("from")
        dest = request.query_params.get("to")

        if not src or not dest:
            raise ValueError("from and to are required")

        lat1, lng1 = map(float, src.split(","))
        lat2, lng2 = map(float, dest.split(","))
        
        res = 10
        src_h3 = h3.latlng_to_cell(lat1, lng1, res)
        dest_h3 = h3.latlng_to_cell(lat2, lng2, res)

        cache_key = f"travel-metrics:h3:{src_h3}:{dest_h3}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return Response(cached)

        data = get_travel_metrics(lat1, lng1, lat2, lng2)
        ttl = get_cache_ttl(data["distance"], data["detour_index"])
        cache.set(cache_key, data, ttl)
        return Response(data)
