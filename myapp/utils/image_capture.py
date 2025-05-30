import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class ImageCapture:
    """Класс для создания и сохранения изображений на разных этапах симуляции"""

    @staticmethod
    def save_simulation_images(mapdl, result, simulation_id, simulation_dir):
        """Централизованный метод для сохранения всех типов изображений"""
        images = {}

        # Сетка
        mesh_path = os.path.join(simulation_dir, 'mesh.png')
        if ImageCapture.capture_mesh(mapdl, mesh_path):
            images['mesh_image'] = mesh_path

        # Результаты
        stress_path = os.path.join(simulation_dir, 'stress.png')
        if ImageCapture.capture_stress(result, stress_path):
            images['stress_image'] = stress_path

        deformation_path = os.path.join(simulation_dir, 'deform.png')
        if ImageCapture.capture_deformation(result, deformation_path):
            images['deformation_image'] = deformation_path

        return images

    @staticmethod
    def capture_geometry(mapdl, save_path, window_size=[1920, 1080]):
        """Захват изображения геометрии модели"""
        try:
            # Переключение в режим препроцессора для визуализации геометрии
            mapdl.prep7()

            # Создание и сохранение изображения
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            mapdl.aplot(background='w', show_edges=True, smooth_shading=True,
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
    def capture_stress(result, save_path, result_type='stress', window_size=[1920, 1080]):
        """Захват изображения результатов симуляции  """
        try:
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            result.plot_principal_nodal_stress(0, 'seqv', background='W', show_edges=True, text_color='k',
                                                   add_text=True,
                                                   window_size=[1920, 1080], screenshot=save_path,
                                                   off_screen=True)
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            plt.close()
            return save_path
        except Exception as e:
            print(f"Ошибка при создании изображения stress: {e}")
            return None

    @staticmethod
    def capture_deformation(mapdl, save_path, window_size=[1920, 1080]):
        """Захват изображения результатов симуляции"""
        try:
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            mapdl.plot_nodal_displacement(0, 'NORM', background='W', show_edges=True, text_color='k',
                                               add_text=True,
                                               window_size=[1920, 1080], screenshot=save_path,
                                               off_screen=True)
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            plt.close()
            return save_path
        except Exception as e:
            print(f"Ошибка при создании изображения результатов: {e}")
            return None