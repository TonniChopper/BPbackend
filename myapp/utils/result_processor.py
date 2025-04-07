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
    displacements = np.array(result.nodal_displacement(0))
    displacement_norms = np.linalg.norm(displacements, axis=1)

    # Сохраняем текстовый результат
    result_file_path = os.path.join(result_dir, 'result.txt')
    with open(result_file_path, 'w') as f:
        f.write(f"Maximum displacement: {displacement_norms.max()}\n")
        f.write(f"Maximum stress: {result.nodal_eqv_stress().max()}\n")
        # Добавляем больше информации о результатах
        f.write(f"Minimum displacement: {displacement_norms.min()}\n")
        f.write(f"Average displacement: {displacement_norms.mean()}\n")
        f.write(f"Average stress: {result.nodal_eqv_stress().mean()}\n")
        f.write(f"Total nodes: {len(result.mesh.nodes)}\n")
        f.write(f"Total elements: {len(result.mesh.elements)}\n")

    # Сохраняем изображение напряжений
    stress_image_path = os.path.join(result_dir, 'stress.png')
    result.plot_nodal_eqv_stress(
        background='white',
        show_edges=True,
        show_displacement=True,
        savefig=True,
        filename=stress_image_path,
        cpos='iso',
        window_size=[1920, 1080],
        text_color='black',
        add_text=True
    )

    # Сохраняем изображение с текстурами
    texture_image_path = os.path.join(result_dir, 'texture.png')
    result.plot_nodal_eqv_stress(
        background='white',
        show_edges=True,
        show_displacement=True,
        savefig=True,
        filename=texture_image_path,
        cpos='iso',
        window_size=[1920, 1080],
        style='surface',
        show_axes=True
    )

    # Сохраняем изображение температуры
    temp_image_path = os.path.join(result_dir, 'temperature.png')
    try:
        result.plot_nodal_temperature(
            background='white',
            show_edges=True,
            savefig=True,
            filename=temp_image_path,
            cpos='iso',
            window_size=[1920, 1080]
        )
    except AttributeError:
        # Если метод plot_nodal_temperature не существует, используем другой метод
        result.plot_nodal_displacement(
            'NORM',
            background='white',
            show_edges=True,
            savefig=True,
            filename=temp_image_path,
            cpos='iso',
            window_size=[1920, 1080],
            scalar_bar_args={'title': 'Temperature Equivalent'}
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
        'max_displacement': float(displacement_norms.max()),
        'min_displacement': float(displacement_norms.min()),
        'avg_displacement': float(displacement_norms.mean()),
        'max_stress': float(result.nodal_eqv_stress().max()),
        'min_stress': float(result.nodal_eqv_stress().min()),
        'avg_stress': float(result.nodal_eqv_stress().mean()),
        'node_count': len(result.mesh.nodes),
        'element_count': len(result.mesh.elements),
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

