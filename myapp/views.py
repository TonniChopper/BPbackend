from rest_framework import generics
from .models import Graph
from .serializers import GraphSerializer
from .utils import run_simulation
from .tasks import generate_graph
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
from django.conf import settings

# class SimulationListCreate(generics.ListCreateAPIView):
#     queryset = Simulation.objects.all()
#     serializer_class = SimulationSerializer
#
#     def perform_create(self, serializer):
#         simulation = serializer.save()
#         result_data, result_image_path = run_simulation(simulation.pressure, simulation.temperature)
#         simulation.result_data = result_data
#         simulation.result_image = result_image_path
#         simulation.save()
#
# class SimulationDetail(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Simulation.objects.all()
#     serializer_class = SimulationSerializer
class TriggerTask(APIView):
    def post(self, request, graph_id):
        generate_graph.delay(graph_id)
        return Response({'status': 'Task has been triggered'}, status=status.HTTP_202_ACCEPTED)
class GraphListCreate(generics.ListCreateAPIView):
    queryset = Graph.objects.all()
    serializer_class = GraphSerializer

    def perform_create(self, serializer):
        graph = serializer.save()
        result_data, result_image_path = run_simulation(graph.pressure, graph.temperature)
        graph.image = os.path.relpath(result_image_path, settings.MEDIA_ROOT)
        graph.save()

class GraphDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Graph.objects.all()
    serializer_class = GraphSerializer

    def get_object(self):
        return super().get_object()