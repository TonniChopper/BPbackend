import logging
import json
import os
from celery import shared_task
from redis import Redis
from django.conf import settings
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_simulation_task_with_redis(self, simulation_id):
    """Run a simulation as a Celery task with Redis status tracking"""
    logger.info(f"Starting simulation task for simulation ID: {simulation_id}")

    # Connect to Redis
    redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
    status_key = f"simulation_status:{simulation_id}"

    try:
        # Import here to avoid circular imports
        from myapp.models import Simulation
        from myapp.services.simulation_service import SimulationService
        from myapp.services.simulation_cache_service import SimulationCacheService

        # Get simulation
        simulation = Simulation.objects.get(id=simulation_id)

        # Update Redis status
        redis_client.set(status_key, "RUNNING", ex=86400)

        # Run the simulation through service layer
        result = SimulationService.run_simulation(simulation_id)

        # Cache this result for future use only if successful
        if result and simulation.status == 'COMPLETED':
            SimulationCacheService.cache_simulation(simulation_id, simulation.parameters)

        return {"status": "success", "simulation_id": simulation_id}

    except Exception as e:
        logger.error(f"Error in simulation task: {str(e)}", exc_info=True)

        try:
            # Import here to avoid circular imports
            from myapp.models import Simulation

            # Update simulation status in the database
            simulation = Simulation.objects.get(id=simulation_id)
            simulation.status = 'FAILED'
            simulation.save()

            # Update Redis status
            redis_client.set(status_key, "FAILED", ex=86400)

        except Exception as db_error:
            logger.error(f"Failed to update simulation status: {str(db_error)}", exc_info=True)

        return {"status": "error", "error": str(e)}