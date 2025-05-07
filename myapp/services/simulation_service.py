# import os
# import logging
# from django.utils import timezone
# from django.db import transaction
# from .mapdl_handler import MAPDLHandler
# from ..models import Simulation, SimulationResult
# from ..utils.result_processor import process_result
#
# logger = logging.getLogger(__name__)
#
#
# class SimulationService:
#     @staticmethod
#     @transaction.atomic
#     def run_simulation(simulation_id):
#         """
#         Запускает симуляцию и сохраняет результаты
#         """
#         simulation = Simulation.objects.get(id=simulation_id)
#         simulation.status = 'RUNNING'
#         simulation.save()
#
#         mapdl_handler = None
#         try:
#             logger.info(f"Starting simulation {simulation_id} with parameters: {simulation.parameters}")
#
#             mapdl_handler = MAPDLHandler()
#             result = mapdl_handler.run_simulation(simulation.parameters)
#
#             processed_result = process_result(result, simulation_id)
#
#             # Создаем или обновляем результат симуляции
#             SimulationResult.objects.update_or_create(
#                 simulation=simulation,
#                 defaults={
#                     'result_file': processed_result['result_file'],
#                     'stress_image': processed_result['stress_image'],
#                     'texture_image': processed_result['texture_image'],
#                     'stress_model': processed_result['stress_model'],
#                     'texture_model': processed_result['texture_model'],
#                     'summary': processed_result['summary']
#                 }
#             )
#
#             simulation.status = 'COMPLETED'
#             simulation.completed_at = timezone.now()
#             simulation.save()
#
#             logger.info(f"Simulation {simulation_id} completed successfully")
#
#             return simulation.result
#
#         except Exception as e:
#             logger.error(f"Simulation {simulation_id} failed: {str(e)}", exc_info=True)
#             simulation.status = 'FAILED'
#             simulation.save()
#             raise e
#         finally:
#             # Закрываем соединение с MAPDL
#             if mapdl_handler:
#                 mapdl_handler.close_mapdl()
#                 logger.info("MAPDL session closed")

#
# import os
# import logging
# from django.utils import timezone
# from django.db import transaction
# from .mapdl_handler import MAPDLHandler
# from ..models import Simulation, SimulationResult
# from ..utils.result_processor import process_result
#
# logger = logging.getLogger(__name__)
#
#
# class SimulationService:
#     @staticmethod
#     @transaction.atomic
#     def run_simulation(simulation_id):
#         """
#         Запускает симуляцию и сохраняет результаты
#         """
#         simulation = Simulation.objects.get(id=simulation_id)
#         simulation.status = 'RUNNING'
#         simulation.save()
#
#         mapdl_handler = None
#         try:
#             logger.info(f"Starting simulation {simulation_id} with parameters: {simulation.parameters}")
#
#             mapdl_handler = MAPDLHandler()
#             mapdl = mapdl_handler.run_simulation(simulation.parameters)
#
#             # Передаем объект mapdl вместо result
#             processed_result = process_result(mapdl, simulation_id)
#
#             # Создаем или обновляем результат симуляции
#             SimulationResult.objects.update_or_create(
#                 simulation=simulation,
#                 defaults={
#                     'result_file': processed_result['result_file'],
#                     'stress_image': processed_result['stress_image'],
#                     'texture_image': processed_result['texture_image'],
#                     'stress_model': processed_result['stress_model'],
#                     'texture_model': processed_result['texture_model'],
#                     'summary': processed_result['summary']
#                 }
#             )
#
#             simulation.status = 'COMPLETED'
#             simulation.completed_at = timezone.now()
#             simulation.save()
#
#             logger.info(f"Simulation {simulation_id} completed successfully")
#
#             return simulation.result
#
#         except Exception as e:
#             logger.error(f"Simulation {simulation_id} failed: {str(e)}", exc_info=True)
#             simulation.status = 'FAILED'
#             simulation.save()
#             raise e
#         finally:
#             # Закрываем соединение с MAPDL
#             if mapdl_handler:
#                 mapdl_handler.close_mapdl()
#                 logger.info("MAPDL session closed")

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
    @transaction.atomic
    def run_simulation(simulation_id):
        """Запускает симуляцию и сохраняет результаты"""
        simulation = Simulation.objects.get(id=simulation_id)
        simulation.status = 'RUNNING'
        simulation.save()

        # Добавляем ID в параметры
        parameters = dict(simulation.parameters)
        parameters['id'] = simulation_id

        mapdl_handler = None
        try:
            logger.info(f"Starting simulation {simulation_id} with parameters: {parameters}")

            mapdl_handler = MAPDLHandler()
            result = mapdl_handler.run_simulation(parameters)

            processor = ResultProcessor()
            processed_result = processor.process_result(result, simulation_id)

            # Создаем или обновляем результат симуляции
            SimulationResult.objects.update_or_create(
                simulation=simulation,
                defaults={
                    'result_file': processed_result['result_file'],
                    'geometry_image': processed_result['geometry_image'],
                    'mesh_image': processed_result['mesh_image'],
                    'results_image': processed_result['results_image'],
                    # 'nodal_stress_image': processed_result['nodal_stress_image'],
                    # 'displacement_image': processed_result['displacement_image'],
                    'nodal_stress_model': processed_result['nodal_stress_model'],
                    'mesh_model': processed_result['mesh_model'],
                    'displacement_model': processed_result['displacement_model'],
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
