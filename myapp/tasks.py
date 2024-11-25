from celery import shared_task
from .models import Graph
from .utils import run_simulation_type_1, run_simulation_type_2, run_simulation_type_3
import os
from django.conf import settings
import redis

@shared_task
def generate_graph(graph_id):
    graph = Graph.objects.get(id=graph_id)
    simulation_id = graph.simulation_id

    simulation_functions = {
        1: run_simulation_type_1,
        2: run_simulation_type_2,
        3: run_simulation_type_3
    }
    if simulation_id in simulation_functions:
        result_data, result_image_path = simulation_functions[simulation_id](graph.pressure, graph.temperature)
    else:
        raise ValueError("Invalid simulation ID")

    graph.image = os.path.relpath(result_image_path, settings.MEDIA_ROOT)
    graph.save()

r = redis.Redis(
    host='redis-12610.c300.eu-central-1-1.ec2.redns.redis-cloud.com',
    port=12610,
    password='euzl8ptRLsx3ielfGGP9th2mLaoWmLtC'
)