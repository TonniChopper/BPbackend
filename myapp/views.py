import os
from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import FileResponse
from .models import Simulation
from .serializers import SimulationSerializer, UserSerializer
from .tasks import run_simulation_task_with_redis
from .utils import run_simulation

class SimulationListCreateView(generics.ListCreateAPIView):
    serializer_class = SimulationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Return simulations only for authenticated users
        if self.request.user.is_authenticated:
            return self.request.user.simulations.all()
        return Simulation.objects.none()

    def perform_create(self, serializer):
        # If the user is authenticated, store the simulation for 2 days;
        # Otherwise, simulation is created without persistence and download
        user = self.request.user if self.request.user.is_authenticated else None
        simulation = serializer.save(user=user)
        # run_simulation(simulation.parameters)
        params = simulation.parameters
        result_file_path = run_simulation(**params)
        # Store the simulation result path into the file field
        simulation.simulation_result = result_file_path
        simulation.save()


class SimulationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SimulationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.simulations.all()

class SimulationResumeView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, format=None):
        try:
            simulation = Simulation.objects.get(pk=pk, user=request.user)
        except Simulation.DoesNotExist:
            return Response({'detail': 'Simulation not found.'}, status=status.HTTP_404_NOT_FOUND)
        if not simulation.is_active:
            return Response({'detail': 'Simulation expired, cannot resume.'}, status=status.HTTP_400_BAD_REQUEST)
        # Restart simulation with saved parameters
        run_simulation(simulation.parameters)
        return Response({'detail': 'Simulation resumed.'}, status=status.HTTP_200_OK)

class SimulationDownloadView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, format=None):
        try:
            simulation = Simulation.objects.get(pk=pk, user=request.user)
        except Simulation.DoesNotExist:
            return Response({'detail': 'Simulation not found.'}, status=status.HTTP_404_NOT_FOUND)
        # If simulation was created by an unauthenticated (ephemeral) user, deny download.
        if simulation.user is None:
            return Response({'detail': 'Download not available for unauthenticated simulation.'},
                            status=status.HTTP_403_FORBIDDEN)
        if simulation.simulation_result:
            file_path = simulation.simulation_result.path
            if os.path.isfile(file_path):
                return FileResponse(
                    open(file_path, 'rb'),
                    as_attachment=True,
                    filename=os.path.basename(file_path)
                )
            return Response({'detail': 'File not found on server.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'detail': 'Simulation result not available.'}, status=status.HTTP_404_NOT_FOUND)


class SimulationStatusView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, format=None):
        """
        Returns current simulation status data including the URL of the snapshot image.
        The frontend can poll this endpoint while the simulation is running.
        """
        try:
            simulation = Simulation.objects.get(pk=pk, user=request.user)
        except Simulation.DoesNotExist:
            return Response({'detail': 'Simulation not found.'}, status=status.HTTP_404_NOT_FOUND)

        status_data = {
            'id': simulation.id,
            'parameters': simulation.parameters,
            'is_active': simulation.is_active,
            # If simulation_result points to an image (e.g. .png), it can be shown as interactive snapshot.
            'snapshot_url': simulation.simulation_result.url if simulation.simulation_result and simulation.simulation_result.path.endswith('.png') else None
        }
        return Response(status_data, status=status.HTTP_200_OK)

class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]