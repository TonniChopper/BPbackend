import matplotlib.pyplot as plt
import numpy as np
import os
from django.conf import settings

def run_simulation_type_1(pressure, temperature):
    x = np.linspace(0, 10, 100)
    y = pressure * np.sin(x) + temperature * np.cos(x)

    plt.figure()
    plt.plot(x, y, 'r-', label=f'Pressure: {pressure}, Temperature: {temperature}')  # Red solid line
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.title('Graph Type 1')
    plt.legend()

    image_path = os.path.join(settings.MEDIA_ROOT, 'simulations', 'result_type_1.png')
    plt.savefig(image_path)
    plt.close()

    result_data = f"Graph Type 1 generated for pressure: {pressure}, temperature: {temperature}"
    return result_data, image_path

def run_simulation_type_2(pressure, temperature):
    x = np.linspace(0, 10, 100)
    y = pressure * np.cos(x) - temperature * np.sin(x)

    plt.figure()
    plt.plot(x, y, 'g--', label=f'Pressure: {pressure}, Temperature: {temperature}')  # Green dashed line
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.title('Graph Type 2')
    plt.legend()

    image_path = os.path.join(settings.MEDIA_ROOT, 'simulations', 'result_type_2.png')
    plt.savefig(image_path)
    plt.close()

    result_data = f"Graph Type 2 generated for pressure: {pressure}, temperature: {temperature}"
    return result_data, image_path

def run_simulation_type_3(pressure, temperature):
    x = np.linspace(0, 10, 100)
    y = pressure * np.tan(x) + temperature * np.tan(x)

    plt.figure()
    plt.plot(x, y, 'b-.', label=f'Pressure: {pressure}, Temperature: {temperature}')  # Blue dash-dot line
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.title('Graph Type 3')
    plt.legend()

    image_path = os.path.join(settings.MEDIA_ROOT, 'simulations', 'result_type_3.png')
    plt.savefig(image_path)
    plt.close()

    result_data = f"Graph Type 3 generated for pressure: {pressure}, temperature: {temperature}"
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