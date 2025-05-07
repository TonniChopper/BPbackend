# import os
# import json
# import numpy as np
# import matplotlib.pyplot as plt
# from django.conf import settings
# from django.core.files.base import ContentFile
#
# def process_result(result, simulation_id):
#     """Обрабатывает результаты MAPDL и сохраняет их в файлы"""
#     result_dir = os.path.join(settings.MEDIA_ROOT, 'simulation_results', str(simulation_id))
#     os.makedirs(result_dir, exist_ok=True)
#
#     # Получаем смещения и вычисляем их нормы
#     displacement_result = result.nodal_displacement(0)
#
#     # Используем простой список Python вместо массива NumPy
#     displacement_norms = []
#     for disp in displacement_result:
#         # Проверяем, что disp - это итерируемый объект (список или кортеж) и не NumPy массив
#         if hasattr(disp, '__iter__') and not isinstance(disp, np.ndarray):
#             norm = np.sqrt(sum(d * d for d in disp))
#         elif isinstance(disp, np.ndarray):
#             # Если disp - это NumPy массив, используем np.linalg.norm
#             norm = np.linalg.norm(disp)
#         else:
#             # Если disp - это скаляр, используем его напрямую
#             norm = abs(disp)
#         displacement_norms.append(norm)
#
#     # Преобразуем список в NumPy массив для более эффективных операций
#     displacement_norms_array = np.array(displacement_norms)
#
#     # Используем методы NumPy для вычисления статистики
#     max_displacement = displacement_norms_array.max()
#     min_displacement = displacement_norms_array.min()
#     avg_displacement = displacement_norms_array.mean()
#
#     # Получаем напряжения
#     nnum, stress = result.principal_nodal_stress(0)
#     von_mises = stress[:, -1]  # von-Mises stress is the right most column
#
#     # Сохраняем текстовый результат
#     result_file_path = os.path.join(result_dir, 'result.txt')
#     with open(result_file_path, 'w') as f:
#         f.write(f"Maximum displacement: {max_displacement}\n")
#         f.write(f"Maximum stress: {von_mises.max()}\n")
#         f.write(f"Minimum displacement: {min_displacement}\n")
#         f.write(f"Average displacement: {avg_displacement}\n")
#         f.write(f"Average stress: {von_mises.mean()}\n")
#         f.write(f"Total nodes: {len(result.mesh.nodes)}\n")
#         f.write(f"Total elements: {len(result.mesh.enum)}\n")  # Используем enum вместо elements
#
#     # Сохраняем изображение напряжений
#     stress_image_path = os.path.join(result_dir, 'displacement.png')
#     result.plot_nodal_solution(
#         0,  # Используем '1' для первого главного напряжения
#              'x',
#         label = 'Displacement',
#              background='white',
#              show_edges=True,
#              show_displacement=True,
#              # filename=stress_image_path,
#             screenshot=stress_image_path,
#              cpos='iso',
#              window_size=[1920,1080],
#              text_color='black',
#         add_text=True,
#         interactive = False,
#     )
#
#     # Сохраняем изображение с текстурами
#     texture_image_path = os.path.join(result_dir, 'stress.png')
#     result.plot_nodal_stress(
#         'SEQV',
#         label='Stress',
#         background='white',
#         show_edges=True,
#         show_displacement=True,
#         # filename=stress_image_path,
#         screenshot=texture_image_path,
#         cpos='iso',
#         window_size=[1920, 1080],
#         text_color='black',
#         add_text=True,
#         interactive=False,
#     )
#
#     # # Экспортируем 3D модели
#     stress_model_path = os.path.join(result_dir, 'stress_model.glb')
#     texture_model_path = os.path.join(result_dir, 'texture_model.glb')
#     temp_model_path = os.path.join(result_dir, 'temp_model.glb')
#
#     try:
#         result.graphics.export_model(stress_model_path, 'glb')
#     except Exception as e:
#         stress_model_path = None
#         print(f"Failed to export stress 3D model: {e}")
#
#     try:
#         result.graphics.export_model(texture_model_path, 'glb')
#     except Exception as e:
#         texture_model_path = None
#         print(f"Failed to export texture 3D model: {e}")
#
#     try:
#         result.graphics.export_model(temp_model_path, 'glb')
#     except Exception as e:
#         temp_model_path = None
#         print(f"Failed to export temperature 3D model: {e}")
#
#     # Создаем сводку результатов с дополнительной информацией
#     summary = {
#         'max_displacement': float(max_displacement),
#         'min_displacement': float(min_displacement),
#         'avg_displacement': float(avg_displacement),
#         'max_stress': float(von_mises.max()),
#         'min_stress': float(von_mises.min()),
#         'avg_stress': float(von_mises.mean()),
#         'node_count': len(result.mesh.nodes),
#         'element_count': len(result.mesh.enum),  # Используем enum вместо elements
#         'has_stress_model': stress_model_path is not None,
#         'has_texture_model': texture_model_path is not None
#     }
#
#     # Сохраняем JSON-сводку для быстрого доступа
#     with open(os.path.join(result_dir, 'summary.json'), 'w') as f:
#         json.dump(summary, f, indent=2)
#
#     return {
#         'result_file': result_file_path,
#         'stress_image': stress_image_path,
#         'texture_image': texture_image_path,
#         'stress_model': stress_model_path,
#         'texture_model': texture_model_path,
#         'temp_model': temp_model_path,
#         'summary': summary
#     }
#
#
# import os
# import json
# import numpy as np
# import matplotlib.pyplot as plt
# from django.conf import settings
# from django.core.files.base import ContentFile
#
#
# def process_result(mapdl, simulation_id):
#     """Обрабатывает результаты MAPDL и сохраняет их в файлы"""
#     result_dir = os.path.join(settings.MEDIA_ROOT, 'simulation_results', str(simulation_id))
#     os.makedirs(result_dir, exist_ok=True)
#
#     # Используем post_processing для получения результатов
#     post = mapdl.post_processing
#
#     # Получаем смещения
#     try:
#         displacement = post.nodal_displacement('NORM')
#         max_displacement = displacement.max()
#         min_displacement = displacement.min()
#         avg_displacement = displacement.mean()
#     except Exception as e:
#         print(f"Error getting displacement: {e}")
#         max_displacement = min_displacement = avg_displacement = 0.0
#
#     # Получаем напряжения
#     try:
#         stress = post.nodal_eqv_stress()
#         max_stress = stress.max()
#         min_stress = stress.min()
#         avg_stress = stress.mean()
#     except Exception as e:
#         print(f"Error getting stress: {e}")
#         max_stress = min_stress = avg_stress = 0.0
#
#     # Сохраняем текстовый результат
#     result_file_path = os.path.join(result_dir, 'result.txt')
#     with open(result_file_path, 'w') as f:
#         f.write(f"Maximum displacement: {max_displacement}\n")
#         f.write(f"Maximum stress: {max_stress}\n")
#         f.write(f"Minimum displacement: {min_displacement}\n")
#         f.write(f"Average displacement: {avg_displacement}\n")
#         f.write(f"Average stress: {avg_stress}\n")
#         f.write(f"Total nodes: {len(mapdl.mesh.nodes)}\n")
#         f.write(f"Total elements: {len(mapdl.mesh.enum)}\n")
#
#     # Сохраняем изображение напряжений
#     stress_image_path = os.path.join(result_dir, 'displacement.png')
#     try:
#         post.plot_nodal_solution(
#             mapdl.post_processing.nodal_displacement('X'),
#             cmap='jet',
#             show_edges=True,
#             screenshot=stress_image_path,
#             # post.plot_nodal_solution(
#         #     0,  # Используем '1' для первого главного напряжения
#         #      'x',
#         # label = 'Displacement',
#         #      background='white',
#         #      show_edges=True,
#         #      show_displacement=True,
#         #      # filename=stress_image_path,
#         #     screenshot=stress_image_path,
#         #      cpos='iso',
#         #      window_size=[1920,1080],
#         #      text_color='black',
#         # add_text=True,
#         # interactive = False,
#         )
#     except Exception as e:
#         print(f"Failed to create stress image: {e}")
#         # Создаем пустое изображение в случае ошибки
#         # plt.figure(figsize=(19.2, 10.8))
#         # plt.text(0.5, 0.5, "Error generating stress visualization",
#         #          horizontalalignment='center', verticalalignment='center')
#         # plt.savefig(stress_image_path)
#         # plt.close()
#
#     # Сохраняем изображение с текстурами
#     texture_image_path = os.path.join(result_dir, 'stress.png')
#     try:
#         post.plot_nodal_stress(
#             'SEQV',
#             label='Stress',
#             background='white',
#             show_edges=True,
#             show_displacement=True,
#             # filename=stress_image_path,
#             screenshot=texture_image_path,
#             cpos='iso',
#             window_size=[1920, 1080],
#             text_color='black',
#             add_text=True,
#             interactive=False,
#         )
#     except Exception as e:
#         print(f"Failed to create texture image: {e}")
#         # Создаем пустое изображение в случае ошибки
#         # plt.figure(figsize=(19.2, 10.8))
#         # plt.text(0.5, 0.5, "Error generating texture visualization",
#         #          horizontalalignment='center', verticalalignment='center')
#         # plt.savefig(texture_image_path)
#         # plt.close()
#
#     # Сохраняем изображение смещений
#     # temp_image_path = os.path.join(result_dir, 'temperature.png')
#     # try:
#     #     post.plot_nodal_displacement(
#     #         'NORM',
#     #         background='white',
#     #         show_edges=True,
#     #         savefig=True,
#     #         filename=temp_image_path,
#     #         cpos='iso',
#     #         window_size=[1920, 1080],
#     #         scalar_bar_args={'title': 'Displacement'}
#     #     )
#     # except Exception as e:
#     #     print(f"Failed to create displacement image: {e}")
#     #     # Создаем пустое изображение в случае ошибки
#     #     plt.figure(figsize=(19.2, 10.8))
#     #     plt.text(0.5, 0.5, "Error generating displacement visualization",
#     #              horizontalalignment='center', verticalalignment='center')
#     #     plt.savefig(temp_image_path)
#     #     plt.close()
#
#     # Экспортируем 3D модели
#     stress_model_path = os.path.join(result_dir, 'stress_model.vtk')
#     texture_model_path = os.path.join(result_dir, 'texture_model.vtk')
#
#     try:
#         # Сохраняем результат в VTK файл
#         mapdl.save('file.rst')
#         mapdl.result.save_as_vtk(stress_model_path)
#     except Exception as e:
#         stress_model_path = None
#         print(f"Failed to export stress 3D model: {e}")
#
#     # Для других моделей используем тот же файл
#     texture_model_path = stress_model_path
#     temp_model_path = stress_model_path
#
#     # Создаем сводку результатов с дополнительной информацией
#     # Обрабатываем возможные NaN или Infinity значения
#     def safe_float(value):
#         try:
#             float_val = float(value)
#             if np.isnan(float_val) or np.isinf(float_val):
#                 return 0.0
#             return float_val
#         except:
#             return 0.0
#
#     summary = {
#         'max_displacement': safe_float(max_displacement),
#         'min_displacement': safe_float(min_displacement),
#         'avg_displacement': safe_float(avg_displacement),
#         'max_stress': safe_float(max_stress),
#         'min_stress': safe_float(min_stress),
#         'avg_stress': safe_float(avg_stress),
#         'node_count': len(mapdl.mesh.nodes),
#         'element_count': len(mapdl.mesh.enum),
#         'has_stress_model': stress_model_path is not None,
#         'has_texture_model': texture_model_path is not None,
#         'has_temp_model': temp_model_path is not None
#     }
#
#     # Сохраняем JSON-сводку для быстрого доступа
#     with open(os.path.join(result_dir, 'summary.json'), 'w') as f:
#         json.dump(summary, f, indent=2)
#
#     return {
#         'result_file': result_file_path,
#         'stress_image': stress_image_path,
#         'texture_image': texture_image_path,
#         'stress_model': stress_model_path,
#         'texture_model': texture_model_path,
#         'summary': summary
#     }

import os
import json
import numpy as np
import matplotlib

matplotlib.use('Agg')  # Неинтерактивный бэкенд
import matplotlib.pyplot as plt
from django.conf import settings
from django.core.files.base import ContentFile
from .image_capture import ImageCapture


class ResultProcessor:
    """Класс для обработки результатов симуляции MAPDL"""

    @staticmethod
    def process_result(result, simulation_id, parameters=None):
        """Обрабатывает результаты MAPDL и сохраняет их в файлы"""
        # Создаем директорию для результатов с корректным ID
        result_dir = os.path.join(settings.MEDIA_ROOT, 'simulation_results', str(simulation_id))
        os.makedirs(result_dir, exist_ok=True)

        # Получаем смещения и вычисляем их нормы
        displacement_result = result.nodal_displacement(0)

        # Используем простой список Python вместо массива NumPy
        displacement_norms = []
        for disp in displacement_result:
            # Проверяем, что disp - это итерируемый объект и не NumPy массив
            if hasattr(disp, '__iter__') and not isinstance(disp, np.ndarray):
                norm = np.sqrt(sum(d * d for d in disp))
            elif isinstance(disp, np.ndarray):
                # Если disp - это NumPy массив, используем np.linalg.norm
                norm = np.linalg.norm(disp)
            else:
                # Если disp - это скаляр, используем его напрямую
                norm = abs(disp)
            displacement_norms.append(norm)

        # Преобразуем список в NumPy массив для более эффективных операций
        displacement_norms_array = np.array(displacement_norms)

        # Используем методы NumPy для вычисления статистики
        max_displacement = displacement_norms_array.max()
        min_displacement = displacement_norms_array.min()
        avg_displacement = displacement_norms_array.mean()

        # Получаем напряжения
        nnum, stress = result.principal_nodal_stress(0)
        von_mises = stress[:, -1]  # von-Mises stress is the right most column

        # Сохраняем текстовый результат
        result_file_path = os.path.join(result_dir, 'result.txt')
        with open(result_file_path, 'w') as f:
            f.write(f"Maximum displacement: {max_displacement}\n")
            f.write(f"Maximum stress: {von_mises.max()}\n")
            f.write(f"Minimum displacement: {min_displacement}\n")
            f.write(f"Average displacement: {avg_displacement}\n")
            f.write(f"Average stress: {von_mises.mean()}\n")
            f.write(f"Total nodes: {len(result.mesh.nodes)}\n")
            f.write(f"Total elements: {len(result.mesh.enum)}\n")

        # Используем сохраненные изображения из mapdl_handler, если они есть
        image_paths = getattr(result, '_image_paths', {})

        # 1. Геометрия
        geometry_image_path = image_paths.get('geometry_image')
        if not geometry_image_path or not os.path.exists(geometry_image_path):
            geometry_image_path = os.path.join(result_dir, 'geometry.png')
            try:
                if hasattr(result, '_mapdl'):
                    ImageCapture.capture_geometry(result._mapdl, geometry_image_path)
                    print("Generated geometry image")
                else:
                    print("Failed geometry image")
                    geometry_image_path = None
            except Exception as e:
                print(f"Failed to create geometry image: {e}")
                geometry_image_path = None

        # 2. Сетка (mesh)
        mesh_image_path = image_paths.get('mesh_image')
        if not mesh_image_path or not os.path.exists(mesh_image_path):
            mesh_image_path = os.path.join(result_dir, 'mesh.png')
            try:
                if hasattr(result, '_mapdl'):
                    ImageCapture.capture_mesh(result._mapdl, mesh_image_path)
                    print("Mesh image saved")
                else:
                    print("Failed to create mesh image")
                    mesh_image_path = None
            except Exception as e:
                print(f"Failed to create mesh image: {e}")
                mesh_image_path = None

        # # 3. Напряжения (nodal stress)
        # nodal_stress_image_path = os.path.join(result_dir, 'nodal_stress.png')
        # try:
        #     result.plot_nodal_stress(
        #         'XY',
        #         background='white',
        #         show_edges=True,
        #         screenshot=nodal_stress_image_path,
        #         cpos='iso',
        #         window_size=(1920, 1080),
        #         off_screen=True
        #     )
        # except Exception as e:
        #     print(f"Failed to create nodal stress image: {e}")
        #     nodal_stress_image_path = None
        #
        # # 4. Смещения (displacement)
        # displacement_image_path = os.path.join(result_dir, 'displacement.png')
        # try:
        #     result.plot_nodal_displacement(
        #         'NORM',
        #         background='white',
        #         show_edges=True,
        #         screenshot=displacement_image_path,
        #         cpos='iso',
        #         window_size=(1920, 1080),
        #         off_screen=True
        #     )
        # except Exception as e:
        #     print(f"Failed to create displacement image: {e}")
        #     displacement_image_path = None

        # Экспортируем 3D модели
        nodal_stress_model_path = os.path.join(result_dir, 'nodal_stress_model.vtk')
        mesh_model_path = os.path.join(result_dir, 'mesh_model.vtk')
        displacement_model_path = os.path.join(result_dir, 'displacement_model.vtk')

        try:
            result.save_as_vtk(nodal_stress_model_path)
        except Exception as e:
            nodal_stress_model_path = None
            print(f"Failed to export nodal stress 3D model: {e}")

        # Для других моделей используем тот же файл
        mesh_model_path = nodal_stress_model_path
        displacement_model_path = nodal_stress_model_path

        # Создаем сводку результатов с дополнительной информацией
        # Обрабатываем возможные NaN или Infinity значения
        def safe_float(value):
            try:
                float_val = float(value)
                if np.isnan(float_val) or np.isinf(float_val):
                    return 0.0
                return float_val
            except:
                return 0.0

        summary = {
            'max_displacement': safe_float(max_displacement),
            'min_displacement': safe_float(min_displacement),
            'avg_displacement': safe_float(avg_displacement),
            'max_stress': safe_float(von_mises.max()),
            'min_stress': safe_float(von_mises.min()),
            'avg_stress': safe_float(von_mises.mean()),
            'node_count': len(result.mesh.nodes),
            'element_count': len(result.mesh.enum),
            'has_geometry_image': geometry_image_path is not None,
            'has_mesh_image': mesh_image_path is not None,
            # 'has_nodal_stress_image': nodal_stress_image_path is not None,
            # 'has_displacement_image': displacement_image_path is not None,
            'has_nodal_stress_model': nodal_stress_model_path is not None,
            'has_mesh_model': mesh_model_path is not None,
            'has_displacement_model': displacement_model_path is not None
        }

        # Сохраняем JSON-сводку для быстрого доступа
        with open(os.path.join(result_dir, 'summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)

        # Результаты из этапов симуляции
        results_image_path = image_paths.get('results_image')

        return {
            'result_file': result_file_path,
            'geometry_image': geometry_image_path,
            'mesh_image': mesh_image_path,
            'results_image': results_image_path,
            # 'nodal_stress_image': nodal_stress_image_path,
            # 'displacement_image': displacement_image_path,
            'nodal_stress_model': nodal_stress_model_path,
            'mesh_model': mesh_model_path,
            'displacement_model': displacement_model_path,
            'summary': summary
        }
