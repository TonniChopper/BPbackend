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