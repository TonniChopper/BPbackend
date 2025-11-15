import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from ..models import Simulation
from ..services.simulation_cache_service import SimulationCacheService
from ..constants import OLD_SIMULATION_THRESHOLD_DAYS
from redis import Redis
import json
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task
def clean_old_simulations():
    """
    Clean up old simulations from the database and remove invalid cache entries
    """
    try:
        # Delete simulations older than threshold
        cutoff_date = timezone.now() - timedelta(days=OLD_SIMULATION_THRESHOLD_DAYS)
        old_simulations = Simulation.objects.filter(created_at__lt=cutoff_date)

        count = old_simulations.count()
        if count > 0:
            # Get their hashes before deleting
            redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
            for simulation in old_simulations:
                try:
                    if simulation.parameters_hash:
                        # Check if this hash is in cache
                        cache_key = f"simulation_cache:{simulation.parameters_hash}"
                        cached_data = redis_client.get(cache_key)
                        if cached_data:
                            cached_data = json.loads(cached_data)
                            # If cache points to this simulation, delete it
                            if cached_data.get('source_id') == simulation.id:
                                redis_client.delete(cache_key)
                except Exception as e:
                    logger.error(f"Error cleaning cache for simulation {simulation.id}: {e}")

            # Delete the simulations
            old_simulations.delete()
            logger.info(f"Deleted {count} old simulations")

        return {"cleaned": count}
    except Exception as e:
        logger.error(f"Error in clean_old_simulations task: {e}", exc_info=True)
        return {"error": str(e)}