from celery import shared_task
from .utils import run_simulation
from .models import Graph

@shared_task
def generate_graph(graph_id):
    graph = Graph.objects.get(id=graph_id)
    result_data, result_image_path = run_simulation(graph.pressure, graph.temperature)
    graph.result_data = result_data
    graph.result_image = result_image_path
    graph.save()

import redis

r = redis.Redis(
    host='redis-12610.c300.eu-central-1-1.ec2.redns.redis-cloud.com',
    port=12610,
    password='euzl8ptRLsx3ielfGGP9th2mLaoWmLtC'
)