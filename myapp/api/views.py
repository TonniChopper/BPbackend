import os
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import FileResponse
from rest_framework.views import APIView
from myapp.models import Simulation
from myapp.api.serializers import SimulationSerializer, SimulationResultSerializer, UserSerializer
from myapp.tasks.simulation_task import run_simulation_task_with_redis
from myapp.services.simulation_service import SimulationService

class SimulationListCreateView(generics.ListCreateAPIView):
    serializer_class = SimulationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.request.user.simulations.all()
        return Simulation.objects.filter(user__isnull=True)

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        simulation = serializer.save(user=user, status='PENDING')
        # Запускаем асинхронную задачу вместо синхронного вызова
        # run_simulation_task_with_redis.delay(simulation.id)
        SimulationService.run_simulation(simulation.id)
        return Response(SimulationSerializer(simulation).data, status=status.HTTP_201_CREATED)


class SimulationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SimulationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Simulation.objects.filter(user=self.request.user)


class SimulationResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            simulation = Simulation.objects.get(pk=pk, user=request.user)
            if simulation.status not in ['FAILED', 'COMPLETED']:
                return Response({'detail': 'Simulation cannot be resumed.'}, status=status.HTTP_400_BAD_REQUEST)
            simulation.status = 'PENDING'
            simulation.save()
            # Запускаем асинхронную задачу вместо синхронного вызова
            run_simulation_task_with_redis.delay(simulation.id)
            return Response({'detail': 'Simulation resumed.'}, status=status.HTTP_200_OK)
        except Simulation.DoesNotExist:
            return Response({'detail': 'Simulation not found.'}, status=status.HTTP_404_NOT_FOUND)


class SimulationDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, file_type):
        try:
            simulation = Simulation.objects.get(pk=pk, user=request.user)
            if simulation.status != 'COMPLETED':
                return Response({'detail': 'Simulation results not ready.'}, status=status.HTTP_400_BAD_REQUEST)

            if not hasattr(simulation, 'result'):
                return Response({'detail': 'No results found for this simulation.'}, status=status.HTTP_404_NOT_FOUND)

            try:
                if file_type == 'result':
                    file_path = simulation.result.result_file.path
                    filename = f'simulation_{pk}_result.txt'
                    content_type = 'text/plain'
                elif file_type == 'stress_image':
                    file_path = simulation.result.stress_image.path
                    filename = f'simulation_{pk}_stress.png'
                    content_type = 'image/png'
                elif file_type == 'texture_image':
                    file_path = simulation.result.texture_image.path
                    filename = f'simulation_{pk}_texture.png'
                    content_type = 'image/png'
                elif file_type == 'temp_image':
                    file_path = simulation.result.temp_image.path
                    filename = f'simulation_{pk}_temperature.png'
                    content_type = 'image/png'
                elif file_type == 'stress_model':
                    if not simulation.result.stress_model:
                        return Response({'detail': 'Stress 3D model not available.'}, status=status.HTTP_404_NOT_FOUND)
                    file_path = simulation.result.stress_model.path
                    filename = f'simulation_{pk}_stress_model.glb'
                    content_type = 'model/gltf-binary'
                elif file_type == 'texture_model':
                    if not simulation.result.texture_model:
                        return Response({'detail': 'Texture 3D model not available.'}, status=status.HTTP_404_NOT_FOUND)
                    file_path = simulation.result.texture_model.path
                    filename = f'simulation_{pk}_texture_model.glb'
                    content_type = 'model/gltf-binary'
                elif file_type == 'temp_model':
                    if not simulation.result.temp_model:
                        return Response({'detail': 'Temperature 3D model not available.'}, status=status.HTTP_404_NOT_FOUND)
                    file_path = simulation.result.temp_model.path
                    filename = f'simulation_{pk}_temperature_model.glb'
                    content_type = 'model/gltf-binary'
                elif file_type == 'summary':
                    file_path = simulation.result.summary.path
                    filename = f'simulation_{pk}_summary.json'
                    content_type = 'application/json'
                else:
                    return Response({'detail': 'Invalid file type.'}, status=status.HTTP_400_BAD_REQUEST)

                if os.path.exists(file_path):
                    return FileResponse(
                        open(file_path, 'rb'),
                        as_attachment=True,
                        filename=filename,
                        content_type=content_type
                    )
                else:
                    return Response({'detail': 'File not found on server.'}, status=status.HTTP_404_NOT_FOUND)
            except (AttributeError, ValueError) as e:
                return Response({'detail': f'Error accessing file: {str(e)}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Simulation.DoesNotExist:
            return Response({'detail': 'Simulation not found.'}, status=status.HTTP_404_NOT_FOUND)


class SimulationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            simulation = Simulation.objects.get(pk=pk, user=request.user)
            data = {
                'id': simulation.id,
                'status': simulation.status,
                'created_at': simulation.created_at,
                'completed_at': simulation.completed_at,
                'parameters': simulation.parameters,
            }

            if simulation.status == 'COMPLETED' and hasattr(simulation, 'result'):
                data['result_summary'] = simulation.result.summary
                data['has_stress_image'] = bool(simulation.result.stress_image)
                data['has_texture_image'] = bool(simulation.result.texture_image)
                data['has_temp_image'] = bool(simulation.result.temp_image)
                data['has_stress_model'] = bool(simulation.result.stress_model)
                data['has_texture_model'] = bool(simulation.result.texture_model)
                data['has_temp_model'] = bool(simulation.result.temp_model)
                data['stress_image_url'] = request.build_absolute_uri(
                    simulation.result.stress_image.url) if simulation.result.stress_image else None
                data['texture_image_url'] = request.build_absolute_uri(
                    simulation.result.texture_image.url) if simulation.result.texture_image else None
                data['temp_image_url'] = request.build_absolute_uri(
                    simulation.result.temp_image.url) if simulation.result.temp_image else None

            return Response(data)
        except Simulation.DoesNotExist:
            return Response({'detail': 'Simulation not found.'}, status=status.HTTP_404_NOT_FOUND)
class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]