# services/travel_metrics.py
import requests
from core import settings

from core.utils import haversine, haversine_m

MAPBOX_TIMEOUT = 5
OSRM_TIMEOUT = 3
OSRM_TRAFFIC_BUFFER_SEC = 360  # 6 minutes


def detour_index(network_m, straight_m):
    if straight_m == 0:
        return 1.0
    return max(1.0, network_m / straight_m)


def buffer_sec(duration_sec, di):
    """
    Base: 10%
    Extra: +5% per 0.1 above DI 1.2
    Floor: 3 min
    Cap: 10 min
    """
    extra = max(0, di - 1.2)
    factor = 0.10 + (extra * 0.5)
    buffer = int(duration_sec * factor)
    return min(600, max(180, buffer))


def mapbox_metrics(lat1, lng1, lat2, lng2):
    url = (
        "https://api.mapbox.com/directions/v5/mapbox/"
        f"driving-traffic/{lng1},{lat1};{lng2},{lat2}"
    )
    r = requests.get(
        url,
        params={
            "access_token": settings.MAPBOX_TOKEN,
            "overview": "simplified",
            "geometries": "geojson",
        },
        timeout=MAPBOX_TIMEOUT,
    )
    r.raise_for_status()
    route = r.json()["routes"][0]
    net_m = route["distance"]
    base_sec = route["duration"]
    straight_m = haversine(lat1, lng1, lat2, lng2)
    di = detour_index(net_m, straight_m)

    return {
        "distance": net_m,
        "duration": base_sec + buffer_sec(base_sec, di),
        "detour_index": round(di, 2),
        "coordinates": route["geometry"]["coordinates"],
        "provider": "mapbox+di",
    }


def osrm_metrics(lat1, lng1, lat2, lng2):
    """
    Adapts automatically to city morphology
    No magic fixed minutes
    Explains variance in ETA (great for debugging & analytics)
    Fits perfectly with your EAT min/max envelope
    """


    url = f"http://router.project-osrm.org/route/v1/driving/{lng1},{lat1};{lng2},{lat2}"
    r = requests.get(
        url,
        params={"overview": "simplified", "geometries": "geojson"},
        timeout=OSRM_TIMEOUT,
    )
    r.raise_for_status()
    route = r.json()["routes"][0]
    net_m = route["distance"]
    base_sec = route["duration"]

    straight_m = haversine_m(lat1, lng1, lat2, lng2)
    di = detour_index(net_m, straight_m)

    return {
        "distance": net_m,
        "duration": base_sec
        + buffer_sec(base_sec, di)
        + (5 * 60),  # +5 min possible delay
        "detour_index": round(di, 2),
        "coordinates": route["geometry"]["coordinates"],
        "provider": "osrm+di",
    }


def get_travel_metrics(lat1, lng1, lat2, lng2):
    try:
        return mapbox_metrics(lat1, lng1, lat2, lng2)
    except Exception:
        return osrm_metrics(lat1, lng1, lat2, lng2)
