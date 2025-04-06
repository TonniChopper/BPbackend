import os
import logging
import redis
from celery import shared_task
from django.conf import settings
from ..models import Simulation
from ..services.simulation_service import SimulationService

logger = logging.getLogger(__name__)

# Получаем настройки Redis из переменных окружения или используем значения по умолчанию
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis-12610.c300.eu-central-1-1.ec2.redns.redis-cloud.com')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 12610))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', 'euzl8ptRLsx3ielfGGP9th2mLaoWmLtC')

# Setup Redis connection
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)


@shared_task(bind=True, max_retries=3)
def run_simulation_task_with_redis(self, simulation_id):
    """
    Celery task to run simulation, update progress,
    and cache the final result path in Redis.
    """
    try:
        # Обновляем статус в Redis
        redis_key = f"simulation_status:{simulation_id}"
        redis_client.set(redis_key, "RUNNING", ex=86400)  # Хранить 24 часа

        # Запускаем симуляцию через сервисный слой
        result = SimulationService.run_simulation(simulation_id)

        # Обновляем статус в Redis
        redis_client.set(redis_key, "COMPLETED", ex=86400)

        # Сохраняем пути к файлам результатов в Redis
        if result:
            result_data = {
                "result_file": result.result_file.url if result.result_file else None,
                "stress_image": result.stress_image.url if result.stress_image else None,
                "texture_image": result.texture_image.url if result.texture_image else None,
                "temp_image": result.temp_image.url if result.temp_image else None,
                "stress_model": result.stress_model.url if result.stress_model else None,
                "texture_model": result.texture_model.url if result.texture_model else None,
                "temp_model": result.temp_model.url if result.temp_model else None,
                "summary": result.summary
            }
            redis_client.set(
                f"simulation_result:{simulation_id}",
                str(result_data),
                ex=86400
            )

        return {'simulation_id': simulation_id, 'status': 'COMPLETED'}

    except Exception as e:
        logger.error(f"Error during simulation {simulation_id}: {e}", exc_info=True)
        # Обновляем статус в Redis
        redis_client.set(f"simulation_status:{simulation_id}", "FAILED", ex=86400)
        # Повторяем задачу с экспоненциальной задержкой
        self.retry(exc=e, countdown=2 ** self.request.retries * 60)
        return {'simulation_id': simulation_id, 'status': 'FAILED', 'error': str(e)}