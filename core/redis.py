# services/courier_tracker.py
import json
import time
from django.core.cache import cache
from redis.exceptions import RedisError
import logging

logger = logging.getLogger(__name__)


class CourierTracker:
    def __init__(self):
        self.redis = cache.client.get_client()
        self.geo_key = "couriers:geo"
        self.heartbeat_ttl = 45  # seconds

    def update_location(self, courier_id, lng, lat):
        try:
            pipeline = self.redis.pipeline()
            pipeline.geoadd(self.geo_key, {courier_id: (lng, lat)})
            pipeline.set(f"courier:{courier_id}:hb", 1, ex=self.heartbeat_ttl)
            pipeline.execute()
            return True
        except RedisError as e:
            logger.error(f"Failed to update courier {courier_id} location: {e}")
            return False

    def get_active_courier_ids(self):
        """
        Get all courier IDs with active heartbeats
        """
        try:
            # Pattern match to find heartbeat keys
            heartbeat_keys = self.redis.keys("courier:*:heartbeat")

            # Extract courier IDs from keys
            courier_ids = []
            for key in heartbeat_keys:
                # key format: "courier:123:heartbeat"
                parts = key.decode().split(":")
                if len(parts) == 3:
                    courier_ids.append(parts[1])

            return courier_ids

        except RedisError as e:
            logger.error(f"Failed to get active couriers: {e}")
            return []

    def find_nearby_couriers(self, lng, lat, radius_meters=1000):
        # Include distance in results
        nearby = self.redis.georadius(
            self.geo_key, lng, lat, radius_meters, unit="m", withdist=True, sort="ASC"  # Add this
        )

        if not nearby:
            return []

        # nearby is now list of [member, distance]
        pipe = self.redis.pipeline()
        for cid, dist in nearby:
            pipe.exists(f"courier:{cid.decode()}:heartbeat")

        heartbeat_results = pipe.execute()

        active = []
        for (cid, dist), is_alive in zip(nearby, heartbeat_results):
            if is_alive:
                active.append({"id": int(cid.decode()), "distance": dist})
        return active

    def cleanup_inactive_couriers(self):
        """
        Remove inactive couriers from GEO index (run periodically)
        """
        try:
            # Get all couriers in GEO index
            all_couriers = self.redis.zrange(self.geo_key, 0, -1)

            pipeline = self.redis.pipeline()
            removed_count = 0

            for courier_id in all_couriers:
                courier_id = courier_id.decode()
                heartbeat_key = f"courier:{courier_id}:heartbeat"

                # If heartbeat expired, remove from GEO index
                if not self.redis.exists(heartbeat_key):
                    pipeline.zrem(self.geo_key, courier_id)
                    removed_count += 1

            if removed_count > 0:
                pipeline.execute()

            return removed_count

        except RedisError as e:
            logger.error(f"Failed to cleanup inactive couriers: {e}")
            return 0
