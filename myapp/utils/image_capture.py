import os
import numpy as np
from matplotlib import pyplot as plt


class ImageCapture:
    """Класс для создания и сохранения изображений на разных этапах симуляции"""

    @staticmethod
    def capture_geometry(mapdl, save_path, window_size=[1920, 1080]):
        """Захват изображения геометрии модели"""
        try:
            # Переключение в режим препроцессора для визуализации геометрии
            mapdl.prep7()

            # Создание и сохранение изображения
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            mapdl.vplot(
                vtk=True,
                quality=9,
                show_bounds=True,
                background='white',
                cpos='iso',
                screenshot=save_path,
                off_screen=True
            )
            plt.close()
            return save_path
        except Exception as e:
            print(f"Ошибка при создании изображения геометрии: {e}")
            return None

    @staticmethod
    def capture_mesh(mapdl, save_path, window_size=[1920, 1080]):
        """Захват изображения сетки модели"""
        try:
            # Создание и сохранение изображения
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            mapdl.eplot(
                vtk=True,
                show_edges=True,
                show_node_numbering=False,
                background='white',
                cpos='iso',
                screenshot=save_path,
                off_screen=True
            )
            plt.close()
            return save_path
        except Exception as e:
            print(f"Ошибка при создании изображения сетки: {e}")
            return None

    @staticmethod
    def capture_results(result, save_path, result_type='displacement', window_size=[1920, 1080]):
        """Захват изображения результатов симуляции"""
        try:
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))

            if result_type == 'displacement':
                result.plot_nodal_displacement(
                    'NORM',
                    background='white',
                    show_edges=True,
                    screenshot=save_path,
                    cpos='iso',
                    window_size=window_size,
                    off_screen=True
                )
            elif result_type == 'stress':
                result.plot_nodal_stress(
                    'SEQV',  # Эквивалентное напряжение по Мизесу
                    background='white',
                    show_edges=True,
                    screenshot=save_path,
                    cpos='iso',
                    window_size=window_size,
                    off_screen=True
                )
            elif result_type == 'strain':
                result.plot_nodal_strain(
                    'EPTO',  # Полная деформация
                    background='white',
                    show_edges=True,
                    screenshot=save_path,
                    cpos='iso',
                    window_size=window_size,
                    off_screen=True
                )

            plt.close()
            return save_path
        except Exception as e:
            print(f"Ошибка при создании изображения результатов: {e}")
            return None
