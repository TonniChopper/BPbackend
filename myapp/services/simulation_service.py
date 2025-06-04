import os
import logging
from django.utils import timezone
from django.db import transaction
from .mapdl_handler import MAPDLHandler
from ..models import Simulation, SimulationResult
from ..utils.result_processor import ResultProcessor

logger = logging.getLogger(__name__)


class SimulationService:
    @staticmethod
    def queue_simulation(simulation_id):
        """Queue a simulation using Celery"""
        # Import the task inside the method to avoid circular imports
        from ..tasks.simulation_task import run_simulation_task_with_redis

        # Directly dispatch the task
        task = run_simulation_task_with_redis.delay(simulation_id)

        # Store the task ID in Redis for later use (like cancellation)
        from redis import Redis
        from django.conf import settings

        redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
        redis_client.set(f"simulation_task_id:{simulation_id}", task.id, ex=86400)  # 24 hours expiry

        return task.id

    @staticmethod
    @transaction.atomic
    def run_simulation(simulation_id):
        """Run a simulation with the given ID, updating its status and saving results."""
        simulation = Simulation.objects.get(id=simulation_id)
        simulation.status = 'RUNNING'
        simulation.save()

        parameters = dict(simulation.parameters)
        parameters['id'] = simulation_id

        mapdl_handler = None
        try:
            logger.info(f"Starting simulation {simulation_id} with parameters: {parameters}")

            mapdl_handler = MAPDLHandler()
            result = mapdl_handler.run_simulation(parameters)

            processor = ResultProcessor()
            processed_result = processor.process_result(result, simulation_id)

            # Create or update the simulation result
            SimulationResult.objects.update_or_create(
                simulation=simulation,
                defaults={
                    'result_file': processed_result['result_file'],
                    'mesh_image': processed_result['mesh_image'],
                    'stress_image': processed_result['stress_image'],
                    'deformation_image': processed_result['deformation_image'],
                    'summary': processed_result['summary']
                }
            )

            simulation.status = 'COMPLETED'
            simulation.completed_at = timezone.now()
            simulation.save()

            logger.info(f"Simulation {simulation_id} completed successfully")

            return simulation.result

        except Exception as e:
            logger.error(f"Simulation {simulation_id} failed: {str(e)}", exc_info=True)
            simulation.status = 'FAILED'
            simulation.save()
            raise e
        finally:
            if mapdl_handler:
                mapdl_handler.close_mapdl()
                logger.info("MAPDL session closed")

    @staticmethod
    def copy_simulation_result(source_id, target_id):
        """Copy simulation result from one simulation to another"""
        source = Simulation.objects.get(id=source_id)
        target = Simulation.objects.get(id=target_id)

        if not hasattr(source, 'result'):
            raise ValueError(f"Source simulation {source_id} has no results")

        source_result = source.result

        # Create new result for target simulation
        SimulationResult.objects.update_or_create(
            simulation=target,
            defaults={
                'result_file': source_result.result_file,
                'mesh_image': source_result.mesh_image,
                'stress_image': source_result.stress_image,
                'deformation_image': source_result.deformation_image,
                'summary': source_result.summary
            }
        )

        target.status = 'COMPLETED'
        target.completed_at = timezone.now()
        target.save()

        logger.info(f"Copied simulation result from {source_id} to {target_id}")
        return target.result