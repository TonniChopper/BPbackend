# myapp/views.py
from rest_framework import generics
from .models import Graph
from .serializers import GraphSerializer
from .utils import run_simulation_type_1, run_simulation_type_2, run_simulation_type_3
import os
from django.conf import settings

class GraphListCreate(generics.ListCreateAPIView):
    queryset = Graph.objects.all()
    serializer_class = GraphSerializer

    def perform_create(self, serializer):
        graph = serializer.save(user=self.request.user)  # Set the user field
        simulation_id = graph.simulation_id

        if simulation_id == 1:
            result_data, result_image_path = run_simulation_type_1(graph.pressure, graph.temperature)
        elif simulation_id == 2:
            result_data, result_image_path = run_simulation_type_2(graph.pressure, graph.temperature)
        elif simulation_id == 3:
            result_data, result_image_path = run_simulation_type_3(graph.pressure, graph.temperature)
        else:
            raise ValueError("Invalid simulation ID")

        graph.image = os.path.relpath(result_image_path, settings.MEDIA_ROOT)
        graph.save()

class GraphDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Graph.objects.all()
    serializer_class = GraphSerializer

    def get_object(self):
        return super().get_object()