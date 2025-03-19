import os
import logging
import redis
from celery import shared_task
from .models import Simulation
from .utils import run_simulation

logger = logging.getLogger(__name__)

# Setup Redis connection using the provided parameters
redis_client = redis.Redis(
    host='redis-12610.c300.eu-central-1-1.ec2.redns.redis-cloud.com',
    port=12610,
    password='euzl8ptRLsx3ielfGGP9th2mLaoWmLtC',
    decode_responses=True
)


@shared_task
def run_simulation_task_with_redis(simulation_id):
    """
    Celery task that runs the simulation and caches the result in Redis.
    """
    try:
        result_data, result_file_path = run_simulation()
        simulation = Simulation.objects.get(pk=simulation_id)
        if result_file_path and os.path.isfile(result_file_path):
            simulation.simulation_result = os.path.relpath(result_file_path)
            simulation.save()
        # Store the simulation result path in Redis with a 1-day expiration
        redis_key = f"simulation_result:{simulation_id}"
        redis_client.set(redis_key, result_file_path, ex=86400)
        return {'simulation_id': simulation_id, 'result_file_path': result_file_path}
    except Exception as e:
        logger.error(f"Error during simulation {simulation_id}: {e}", exc_info=True)
        return {'simulation_id': simulation_id, 'error': str(e)}
