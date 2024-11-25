import matplotlib.pyplot as plt
import numpy as np
import os
from django.conf import settings
from django.template.context_processors import media


def run_simulation(pressure, temperature):
    # Generate some example data
    x = np.linspace(0, 10, 100)
    y = pressure * np.sin(x) + temperature * np.cos(x)

    # Create a plot
    plt.figure()
    plt.plot(x, y, label=f'Pressure: {pressure}, Temperature: {temperature}')
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.title('Simple Graph')
    plt.legend()

    # Save the plot to a file
    image_path = os.path.join(settings.MEDIA_ROOT, 'simulations', 'result.png')
    plt.savefig(image_path)
    plt.close()

    result_data = f"Graph generated for pressure: {pressure}, temperature: {temperature}"
    return result_data, image_path

# import pyansys
#
# def run_simulation(pressure, temperature):
#     # Пример использования pyansys для запуска симуляции
#     ansys = pyansys.launch_mapdl()
#
#     # Пример создания модели
#     ansys.prep7()
#     ansys.k(1, 0, 0, 0)
#     ansys.k(2, 1, 0, 0)
#     ansys.l(1, 2)
#     ansys.et(1, 'LINK1')
#     ansys.r(1, 1)
#     ansys.mp('EX', 1, 210e9)
#     ansys.mp('PRXY', 1, 0.3)
#     ansys.lmesh(1)
#
#     # Пример задания граничных условий
#     ansys.d(1, 'UX', 0)
#     ansys.f(2, 'FX', pressure)
#
#     # Запуск симуляции
#     ansys.solve()
#
#     # Извлечение результатов
#     result = ansys.result
#     stress = result.nodal_stress(0)
#
#     # Генерация графика с использованием pyansys
#     image_path = 'simulations/result.png'
#     result.plot_nodal_stress(0, show_edges=True, savefig=image_path)
#
#     # Завершение работы с ANSYS
#     ansys.exit()
#
#     result_data = f"Simulation result for pressure: {pressure}, temperature: {temperature}"
#     return result_data, image_path