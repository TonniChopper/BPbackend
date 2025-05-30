import logging
import json
import os
from redis import Redis
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from ..services.simulation_service import SimulationService
from ..services.simulation_cache_service import SimulationCacheService
from ..models import Simulation, SimulationResult

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def run_simulation_task_with_redis(self, simulation_id):
    """
    Execute a simulation task with Redis-based caching and status tracking.
    If an identical simulation has been run before, reuse its results.
    """
    redis_client = None
    try:
        # Get the simulation object
        simulation = Simulation.objects.get(pk=simulation_id)
        redis_client = Redis.from_url(settings.CELERY_BROKER_URL)

        # Update status key first thing
        status_key = f"simulation_status:{simulation_id}"
        redis_client.set(status_key, "INITIALIZED", ex=86400)

        # Add hash creation if not already set
        if not simulation.parameters_hash:
            simulation.save()  # This will generate the hash via the save method

        # Check cache for identical parameters using the hash
        cache_data = SimulationCacheService.get_cached_simulation(simulation.parameters)

        if cache_data and cache_data.get('source_id'):
            cached_sim_id = cache_data.get('source_id')
            # Don't use cache if it's referencing itself
            if str(cached_sim_id) != str(simulation_id):
                logger.info(f"Found cached result from simulation {cached_sim_id} for simulation {simulation_id}")

                try:
                    # Get the cached simulation result
                    source_simulation = Simulation.objects.get(pk=cached_sim_id)

                    if hasattr(source_simulation, 'result') and source_simulation.result:
                        source_result = source_simulation.result

                        # Update status to indicate we're copying results
                        redis_client.set(status_key, "COPYING_CACHED_RESULT", ex=86400)

                        # Create or update the simulation result with cached values
                        SimulationResult.objects.update_or_create(
                            simulation=simulation,
                            defaults={
                                'result_file': source_result.result_file,
                                'mesh_image': source_result.mesh_image,
                                'stress_image': source_result.stress_image,
                                'deformation_image': source_result.deformation_image,
                                'summary': source_result.summary
                            }
                        )

                        # Update simulation status
                        simulation.status = 'COMPLETED'
                        simulation.completed_at = timezone.now()
                        simulation.save()

                        # Update Redis status
                        redis_client.set(status_key, "COMPLETED", ex=86400)

                        # Store additional metadata about caching
                        cache_info = {
                            'source_simulation_id': cached_sim_id,
                            'time_saved': str(timezone.now()),
                            'parameters_hash': simulation.parameters_hash
                        }
                        redis_client.set(f"simulation_cache_info:{simulation_id}", json.dumps(cache_info), ex=86400)

                        return {
                            'simulation_id': simulation_id,
                            'status': 'COMPLETED',
                            'cached': True,
                            'source_id': cached_sim_id
                        }
                    else:
                        logger.warning(f"Cached simulation {cached_sim_id} has no results, running new simulation")
                except Simulation.DoesNotExist:
                    logger.warning(f"Cached simulation {cached_sim_id} not found, running new simulation")
                    # Remove invalid cache entry
                    SimulationCacheService.cache_simulation(None, simulation.parameters, ttl=0)

        # No cache hit or invalid cache, run simulation normally
        redis_client.set(status_key, "RUNNING", ex=86400)

        # Run the simulation through service layer
        result = SimulationService.run_simulation(simulation_id)

        # Cache this result for future use only if successful
        if result and simulation.status == 'COMPLETED':
            SimulationCacheService.cache_simulation(simulation_id, simulation.parameters)

            # Update status in Redis
            redis_client.set(status_key, "COMPLETED", ex=86400)

            # Store result paths in Redis for quick access
            result_data = {
                "result_file": result.result_file.name if result.result_file else None,
                "mesh_image": result.mesh_image.name if result.mesh_image else None,
                "stress_image": result.stress_image.name if result.stress_image else None,
                "deformation_image": result.deformation_image.name if result.deformation_image else None,
                "summary": result.summary
            }
            redis_client.set(
                f"simulation_result:{simulation_id}",
                json.dumps(result_data),
                ex=86400
            )

        return {'simulation_id': simulation_id, 'status': simulation.status}

    except Exception as e:
        logger.error(f"Error during simulation {simulation_id}: {e}", exc_info=True)

        try:
            # Update simulation status
            simulation = Simulation.objects.get(pk=simulation_id)
            simulation.status = 'FAILED'
            simulation.save()

            # Update status in Redis
            if not redis_client:
                redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
            redis_client.set(f"simulation_status:{simulation_id}", "FAILED", ex=86400)
            redis_client.set(f"simulation_error:{simulation_id}", str(e), ex=86400)
        except Exception as inner_error:
            logger.error(f"Error updating failure status: {inner_error}")

        # Retry with exponential backoff, for non-deterministic errors
        if "not found" not in str(e).lower() and "does not exist" not in str(e).lower():
            self.retry(exc=e, countdown=2 ** self.request.retries * 60, max_retries=3)

        return {'simulation_id': simulation_id, 'status': 'FAILED', 'error': str(e)}