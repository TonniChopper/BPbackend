import os
import numpy as np
import matplotlib

matplotlib.use('Agg')  # Неинтерактивный бэкенд
import matplotlib.pyplot as plt


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
            mapdl.vplot(background='w', show_edges=True, smooth_shading=True,
                        window_size=[1920, 1080], savefig=save_path,
                        off_screen=True)
            plt.close()
            return save_path
        except Exception as e:
            print(f"Ошибка при создании изображения геометрии: {e}")
            return None

    @staticmethod
    def capture_mesh(mapdl, save_path, window_size=[1920, 1080]):
        """Захват изображения сетки модели"""
        try:
            mapdl.prep7()
            # Создание и сохранение изображения
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            mapdl.eplot(background='w', show_edges=True, smooth_shading=True,
                        window_size=[1920, 1080], savefig=save_path,
                        off_screen=True)
            plt.close()
            return save_path
        except Exception as e:
            print(f"Ошибка при создании изображения сетки: {e}")
            return None

    @staticmethod
    def capture_results(result, save_path, result_type='stress', window_size=[1920, 1080]):
        """Захват изображения результатов симуляции"""
        try:
            #result.post1()
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            #
            # if result_type == 'displacement':
            #     result.plot_nodal_displacement(
            #         'NORM',
            #         background='white',
            #         show_edges=True,
            #         screenshot=save_path,
            #         cpos='iso',
            #         window_size=[1920, 1080],
            #         # window_size=window_size,
            #         off_screen=True
            #     )
            # result_type == 'stress':
            result.plot_principal_nodal_stress(0, 'seqv', background='w', show_edges=True, text_color='k',
                                                   add_text=True,
                                                   window_size=[1920, 1080], screenshot=save_path,
                                                   off_screen=True)
            result.save_as_vtk('triD2.vtk')
            # elif result_type == 'strain':
            #     result.plot_nodal_strain(
            #         'EPTO',  # Полная деформация
            #         background='white',
            #         show_edges=True,
            #         screenshot=save_path,
            #         cpos='iso',
            #         window_size=[1920, 1080],
            #         # window_size=window_size,
            #         off_screen=True
            #     )
            plt.close()
            return save_path
        except Exception as e:
            print(f"Ошибка при создании изображения результатов: {e}")
            return None
