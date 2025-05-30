import hashlib
import json
import logging
from redis import Redis
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

class SimulationCacheService:
    @staticmethod
    def get_params_hash(parameters):
        """Generate a hash from simulation parameters"""
        params_str = json.dumps(parameters, sort_keys=True)
        return hashlib.md5(params_str.encode()).hexdigest()

    @staticmethod
    def get_cached_simulation(parameters):
        """Check if a simulation with these parameters exists in cache"""
        try:
            params_hash = SimulationCacheService.get_params_hash(parameters)
            redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
            cache_key = f"simulation_cache:{params_hash}"

            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            return None
        except Exception as e:
            logger.error(f"Error checking simulation cache: {e}")
            return None

    @staticmethod
    def cache_simulation(simulation_id, parameters, ttl=604800):
        """Cache a simulation for future reuse"""
        try:
            params_hash = SimulationCacheService.get_params_hash(parameters)
            redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
            cache_key = f"simulation_cache:{params_hash}"

            cache_data = {
                'source_id': simulation_id,
                'created_at': str(timezone.now())
            }
            redis_client.set(cache_key, json.dumps(cache_data), ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Error caching simulation: {e}")
            return False