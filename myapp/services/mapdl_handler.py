from ansys.mapdl.core import launch_mapdl
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class MAPDLHandler:
    _instance = None
    _mapdl = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_mapdl(self):
        if self._mapdl is None:
            try:
                run_location = os.path.join(settings.MEDIA_ROOT, 'mapdl_runs')
                os.makedirs(run_location, exist_ok=True)
                self._mapdl = launch_mapdl(run_location=run_location)
                logger.info("MAPDL session started successfully")
            except Exception as e:
                logger.error(f"Failed to start MAPDL: {str(e)}")
                raise
        return self._mapdl

    def run_simulation(self, parameters):
        try:
            mapdl = self.get_mapdl()

            # Очистка предыдущей сессии
            mapdl.clear()
            mapdl.prep7()

            # Настройка параметров симуляции
            mapdl.et(1, 'SOLID186')  # Улучшенный тип элемента
            mapdl.mp('EX', 1, parameters.get('young_modulus', 2e11))
            mapdl.mp('NUXY', 1, parameters.get('poisson_ratio', 0.27))

            # Создание геометрии
            length = parameters.get('length', 5)
            width = parameters.get('width', 2.5)
            depth = parameters.get('depth', 0.1)
            radius = parameters.get('radius', 0.5)
            num = parameters.get('num', 3)

            mapdl.block(0, length, 0, width, 0, depth)

            # Создание отверстий
            for i in range(1, num + 1):
                mapdl.cyl4(i * length / (num + 1), width / 2, radius, '', '', '', depth)

            # Выполняем булевы операции для создания отверстий
            mapdl.vsbv(1, 'ALL')

            # Создание сетки с улучшенными параметрами
            element_size = parameters.get('element_size', length / 20)
            mapdl.esize(element_size)
            mapdl.mshape(1, "3D")  # Улучшение качества сетки
            mapdl.mshkey(0)  # Свободная сетка
            mapdl.vmesh('ALL')

            # Применение граничных условий
            mapdl.nsel('S', 'LOC', 'X', 0)
            mapdl.d('ALL', 'ALL', 0)
            mapdl.nsel('S', 'LOC', 'X', length)
            mapdl.sf('ALL', 'PRES', parameters.get('pressure', 1000))
            mapdl.nsel('ALL')

            mapdl.finish()
            mapdl.slashsolu()

            # Решение
            mapdl.solve()

            # Постобработка
            mapdl.post1()

            result = mapdl.result

            return result

        except Exception as e:
            logger.error(f"MAPDL simulation failed: {str(e)}", exc_info=True)
            raise Exception(f"MAPDL simulation failed: {str(e)}")

    def close_mapdl(self):
        if self._mapdl is not None:
            try:
                self._mapdl.exit()
                self._mapdl = None
                logger.info("MAPDL session closed successfully")
            except Exception as e:
                logger.error(f"Error closing MAPDL: {str(e)}")

    def __del__(self):
        self.close_mapdl()

#
# from ansys.mapdl.core import launch_mapdl
# import os
# import logging
# from django.conf import settings
#
# logger = logging.getLogger(__name__)
#
#
# class MAPDLHandler:
#     _instance = None
#     _mapdl = None
#
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super().__new__(cls)
#         return cls._instance
#
#     def get_mapdl(self):
#         if self._mapdl is None:
#             try:
#                 run_location = os.path.join(settings.MEDIA_ROOT, 'mapdl_runs')
#                 os.makedirs(run_location, exist_ok=True)
#                 self._mapdl = launch_mapdl(run_location=run_location)
#                 logger.info("MAPDL session started successfully")
#             except Exception as e:
#                 logger.error(f"Failed to start MAPDL: {str(e)}")
#                 raise
#         return self._mapdl
#
#     def run_simulation(self, parameters):
#         try:
#             mapdl = self.get_mapdl()
#
#             # Очистка предыдущей сессии
#             mapdl.clear()
#             mapdl.prep7()
#
#             # Настройка параметров симуляции
#             mapdl.et(1, 'SOLID186')  # Улучшенный тип элемента
#             mapdl.mp('EX', 1, parameters.get('young_modulus', 2e11))
#             mapdl.mp('NUXY', 1, parameters.get('poisson_ratio', 0.27))
#
#             # Создание геометрии
#             length = parameters.get('length', 5)
#             width = parameters.get('width', 2.5)
#             depth = parameters.get('depth', 0.1)
#             radius = parameters.get('radius', 0.5)
#             num = parameters.get('num', 3)
#
#             mapdl.block(0, length, 0, width, 0, depth)
#
#             # Создание отверстий
#             for i in range(1, num + 1):
#                 mapdl.cyl4(i * length / (num + 1), width / 2, radius, '', '', '', depth)
#
#             # Выполняем булевы операции для создания отверстий
#             mapdl.vsbv(1, 'ALL')
#
#             # Создание сетки с улучшенными параметрами
#             element_size = parameters.get('element_size', length / 20)
#             mapdl.esize(element_size)
#             mapdl.mshape(1, "3D")  # Улучшение качества сетки
#             mapdl.mshkey(0)  # Свободная сетка
#             mapdl.vmesh('ALL')
#
#             # Применение граничных условий
#             mapdl.nsel('S', 'LOC', 'X', 0)
#             mapdl.d('ALL', 'ALL', 0)
#             mapdl.nsel('S', 'LOC', 'X', length)
#             mapdl.sf('ALL', 'PRES', parameters.get('pressure', 1000))
#             mapdl.nsel('ALL')
#
#             mapdl.finish()
#             mapdl.slashsolu()
#
#             # Решение
#             mapdl.solve()
#
#             # Постобработка
#             mapdl.post1()
#
#             # Возвращаем сам объект mapdl вместо result
#             return mapdl
#
#         except Exception as e:
#             logger.error(f"MAPDL simulation failed: {str(e)}", exc_info=True)
#             raise Exception(f"MAPDL simulation failed: {str(e)}")
#
#     def close_mapdl(self):
#         if self._mapdl is not None:
#             try:
#                 self._mapdl.exit()
#                 self._mapdl = None
#                 logger.info("MAPDL session closed successfully")
#             except Exception as e:
#                 logger.error(f"Error closing MAPDL: {str(e)}")
#
#     def __del__(self):
#         self.close_mapdl()
