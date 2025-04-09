import os
import json
import numpy as np
import matplotlib.pyplot as plt
from django.conf import settings
from django.core.files.base import ContentFile

def process_result(result, simulation_id):
    """Обрабатывает результаты MAPDL и сохраняет их в файлы"""
    result_dir = os.path.join(settings.MEDIA_ROOT, 'simulation_results', str(simulation_id))
    os.makedirs(result_dir, exist_ok=True)

    # Получаем смещения и вычисляем их нормы
    displacement_result = result.nodal_displacement(0)

    # Используем простой список Python вместо массива NumPy
    displacement_norms = []
    for disp in displacement_result:
        # Проверяем, что disp - это итерируемый объект (список или кортеж) и не NumPy массив
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
        f.write(f"Total elements: {len(result.mesh.enum)}\n")  # Используем enum вместо elements

    # Сохраняем изображение напряжений
    stress_image_path = os.path.join(result_dir, 'stress.png')
    result.plot_principal_nodal_stress(
         0,  # Используем '1' для первого главного напряжения
        'S1',
        background='white',
        show_edges=True,
        show_displacement=True,
        savefig=True,
        filename=stress_image_path,
        cpos='iso',
        window_size=[1920,1080],
        text_color='black',
        add_text=True
    )

    # Сохраняем изображение с текстурами
    texture_image_path = os.path.join(result_dir, 'texture.png')
    result.plot_principal_nodal_stress(
         1,  # Используем '2' для второго главного напряжения
        'S2',
        background='white',
        show_edges=True,
        show_displacement=True,
        savefig=True,
        filename=texture_image_path,
        cpos='iso',
        window_size=[1920,1080],
        style='surface',
        show_axes=True
    )

    # Сохраняем изображение температуры или эквивалентного напряжения
    temp_image_path = os.path.join(result_dir, 'temperature.png')
    try:
        result.plot_nodal_temperature(
            background='white',
            show_edges=True,
            savefig=True,
            filename=temp_image_path,
            cpos='iso',
            window_size=[1920,1080]
        )
    except AttributeError:
        # Используем третье главное напряжение вместо температуры
        result.plot_principal_nodal_stress(
            3,  # Используем '3' для третьего главного напряжения
            'SEQV',
            background='white',
            show_edges=True,
            savefig=True,
            filename=temp_image_path,
            cpos='iso',
            window_size=[1920,1080],
            scalar_bar_args={'title': 'Third Principal Stress'}
        )

    # Экспортируем 3D модели
    stress_model_path = os.path.join(result_dir, 'stress_model.glb')
    texture_model_path = os.path.join(result_dir, 'texture_model.glb')
    temp_model_path = os.path.join(result_dir, 'temp_model.glb')

    try:
        result.graphics.export_model(stress_model_path, 'glb')
    except Exception as e:
        stress_model_path = None
        print(f"Failed to export stress 3D model: {e}")

    try:
        result.graphics.export_model(texture_model_path, 'glb')
    except Exception as e:
        texture_model_path = None
        print(f"Failed to export texture 3D model: {e}")

    try:
        result.graphics.export_model(temp_model_path, 'glb')
    except Exception as e:
        temp_model_path = None
        print(f"Failed to export temperature 3D model: {e}")

    # Создаем сводку результатов с дополнительной информацией
    summary = {
        'max_displacement': float(max_displacement),
        'min_displacement': float(min_displacement),
        'avg_displacement': float(avg_displacement),
        'max_stress': float(von_mises.max()),
        'min_stress': float(von_mises.min()),
        'avg_stress': float(von_mises.mean()),
        'node_count': len(result.mesh.nodes),
        'element_count': len(result.mesh.enum),  # Используем enum вместо elements
        'has_stress_model': stress_model_path is not None,
        'has_texture_model': texture_model_path is not None,
        'has_temp_model': temp_model_path is not None
    }

    # Сохраняем JSON-сводку для быстрого доступа
    with open(os.path.join(result_dir, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

    return {
        'result_file': result_file_path,
        'stress_image': stress_image_path,
        'texture_image': texture_image_path,
        'temp_image': temp_image_path,
        'stress_model': stress_model_path,
        'texture_model': texture_model_path,
        'temp_model': temp_model_path,
        'summary': summary
    }
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
#     stress_image_path = os.path.join(result_dir, 'stress.png')
#     try:
#         post.plot_nodal_eqv_stress(
#             background='white',
#             show_edges=True,
#             show_displacement=True,
#             savefig=True,
#             filename=stress_image_path,
#             cpos='iso',
#             window_size=[1920, 1080],
#             text_color='black',
#             add_text=True
#         )
#     except Exception as e:
#         print(f"Failed to create stress image: {e}")
#         # Создаем пустое изображение в случае ошибки
#         plt.figure(figsize=(19.2, 10.8))
#         plt.text(0.5, 0.5, "Error generating stress visualization",
#                  horizontalalignment='center', verticalalignment='center')
#         plt.savefig(stress_image_path)
#         plt.close()
#
#     # Сохраняем изображение с текстурами
#     texture_image_path = os.path.join(result_dir, 'texture.png')
#     try:
#         post.plot_nodal_principal_stress(
#             'S1',
#             background='white',
#             show_edges=True,
#             show_displacement=True,
#             savefig=True,
#             filename=texture_image_path,
#             cpos='iso',
#             window_size=[1920, 1080],
#             style='surface',
#             show_axes=True
#         )
#     except Exception as e:
#         print(f"Failed to create texture image: {e}")
#         # Создаем пустое изображение в случае ошибки
#         plt.figure(figsize=(19.2, 10.8))
#         plt.text(0.5, 0.5, "Error generating texture visualization",
#                  horizontalalignment='center', verticalalignment='center')
#         plt.savefig(texture_image_path)
#         plt.close()
#
#     # Сохраняем изображение смещений
#     temp_image_path = os.path.join(result_dir, 'temperature.png')
#     try:
#         post.plot_nodal_displacement(
#             'NORM',
#             background='white',
#             show_edges=True,
#             savefig=True,
#             filename=temp_image_path,
#             cpos='iso',
#             window_size=[1920, 1080],
#             scalar_bar_args={'title': 'Displacement'}
#         )
#     except Exception as e:
#         print(f"Failed to create displacement image: {e}")
#         # Создаем пустое изображение в случае ошибки
#         plt.figure(figsize=(19.2, 10.8))
#         plt.text(0.5, 0.5, "Error generating displacement visualization",
#                  horizontalalignment='center', verticalalignment='center')
#         plt.savefig(temp_image_path)
#         plt.close()
#
#     # Экспортируем 3D модели
#     stress_model_path = os.path.join(result_dir, 'stress_model.vtk')
#     texture_model_path = os.path.join(result_dir, 'texture_model.vtk')
#     temp_model_path = os.path.join(result_dir, 'temp_model.vtk')
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
#         'temp_image': temp_image_path,
#         'stress_model': stress_model_path,
#         'texture_model': texture_model_path,
#         'temp_model': temp_model_path,
#         'summary': summary
#     }

# import os
# import json
# import numpy as np
# import matplotlib.pyplot as plt
# from django.conf import settings
#
#
# def process_result(result, simulation_id):
#     """Обрабатывает результаты MAPDL и сохраняет их в файлы"""
#     result_dir = os.path.join(settings.MEDIA_ROOT, 'simulation_results', str(simulation_id))
#     os.makedirs(result_dir, exist_ok=True)
#
#     # Получаем смещения и вычисляем их нормы
#     nnum, displacement_result = result.nodal_displacement(0)
#
#     # Вычисляем нормы векторов смещения
#     displacement_norms = []
#     for disp in displacement_result:
#         if hasattr(disp, '__iter__') and not isinstance(disp, np.ndarray):
#             norm = np.sqrt(sum(d * d for d in disp))
#         elif isinstance(disp, np.ndarray):
#             norm = np.linalg.norm(disp)
#         else:
#             norm = abs(disp)
#         displacement_norms.append(norm)
#
#     displacement_norms_array = np.array(displacement_norms)
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
#         f.write(f"Total elements: {len(result.mesh.enum)}\n")
#
#     # Сохраняем изображения напрямую через matplotlib
#     # Изображение 1: Напряжения (S1)
#     stress_image_path = os.path.join(result_dir, 'stress.png')
#     try:
#         plt.figure(figsize=(19.2, 10.8))
#         result.plot_principal_nodal_stress(0, 'S1',
#                                            background='white',
#                                            show_edges=True,
#                                            cpos='iso',
#                                            window_size=[1920, 1080],
#                                            text_color='black',
#                                            add_text=True,
#                                            screenshot=stress_image_path)
#         plt.close()
#     except Exception as e:
#         print(f"Failed to create stress image: {e}")
#
#     # Изображение 2: Напряжения с текстурами (S2)
#     texture_image_path = os.path.join(result_dir, 'texture.png')
#     try:
#         plt.figure(figsize=(19.2, 10.8))
#         result.plot_principal_nodal_stress(0, 'S2',
#                                            background='white',
#                                            show_edges=True,
#                                            style='surface',
#                                            cpos='iso',
#                                            window_size=[1920, 1080],
#                                            show_axes=True,
#                                            screenshot=texture_image_path)
#         plt.close()
#     except Exception as e:
#         print(f"Failed to create texture image: {e}")
#
#     # Изображение 3: Эквивалентные напряжения (SEQV)
#     temp_image_path = os.path.join(result_dir, 'temperature.png')
#     try:
#         plt.figure(figsize=(19.2, 10.8))
#         result.plot_principal_nodal_stress(0, 'SEQV',
#                                            background='white',
#                                            show_edges=True,
#                                            cpos='iso',
#                                            window_size=[1920, 1080],
#                                            scalar_bar_args={'title': 'Equivalent Stress'},
#                                            screenshot=temp_image_path)
#         plt.close()
#     except Exception as e:
#         print(f"Failed to create temperature image: {e}")
#
#     # Экспортируем 3D модели
#     stress_model_path = os.path.join(result_dir, 'stress_model.glb')
#     texture_model_path = os.path.join(result_dir, 'texture_model.glb')
#     temp_model_path = os.path.join(result_dir, 'temp_model.glb')
#
#     try:
#         # Сохраняем модель в формате VTK, который затем можно конвертировать в GLB
#         result.save_as_vtk(stress_model_path.replace('.glb', '.vtk'))
#         stress_model_path = stress_model_path.replace('.glb', '.vtk')
#     except Exception as e:
#         stress_model_path = None
#         print(f"Failed to export stress 3D model: {e}")
#
#     try:
#         # Для других моделей делаем то же самое
#         result.save_as_vtk(texture_model_path.replace('.glb', '.vtk'))
#         texture_model_path = texture_model_path.replace('.glb', '.vtk')
#     except Exception as e:
#         texture_model_path = None
#         print(f"Failed to export texture 3D model: {e}")
#
#     try:
#         result.save_as_vtk(temp_model_path.replace('.glb', '.vtk'))
#         temp_model_path = temp_model_path.replace('.glb', '.vtk')
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
#         'element_count': len(result.mesh.enum),
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
#         'temp_image': temp_image_path,
#         'stress_model': stress_model_path,
#         'texture_model': texture_model_path,
#         'temp_model': temp_model_path,
#         'summary': summary
#     }
