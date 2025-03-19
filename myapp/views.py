from rest_framework import generics, permissions, views, status
from rest_framework.authtoken.admin import User
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import FileResponse
from .models import Simulation
from .serializers import SimulationSerializer, UserSerializer
from .tasks import run_simulation_task
import os

class SimulationListCreateView(generics.ListCreateAPIView):
    serializer_class = SimulationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.simulations.all()

    def perform_create(self, serializer):
        simulation = serializer.save(user=self.request.user)
        # Start the simulation asynchronously.
        run_simulation_task.delay(simulation.id)

class SimulationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SimulationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.simulations.all()

class SimulationDownloadView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, format=None):
        try:
            simulation = Simulation.objects.get(pk=pk, user=request.user)
        except Simulation.DoesNotExist:
            return Response({'detail': 'Simulation not found.'}, status=status.HTTP_404_NOT_FOUND)

        if simulation.simulation_result:
            file_path = simulation.simulation_result.path
            if os.path.isfile(file_path):
                return FileResponse(
                    open(file_path, 'rb'),
                    as_attachment=True,
                    filename=os.path.basename(file_path)
                )
            return Response({'detail': 'File not found on server.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'detail': 'No simulation result available.'}, status=status.HTTP_404_NOT_FOUND)

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return User.objects.all()

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.set_password(instance.password)
        instance.save()
