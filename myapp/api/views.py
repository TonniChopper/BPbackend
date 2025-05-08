import os
import json
import tempfile
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
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class SimulationListCreateView(generics.ListCreateAPIView):
    serializer_class = SimulationSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.request.user.simulations.all()
        return Simulation.objects.filter(user__isnull=True)

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            simulation = serializer.save(user=self.request.user)
        else:
            simulation = serializer.save(user=None)
            self.request.session['last_simulation_id'] = simulation.id
            self.request.session.set_expiry(86400)

        SimulationService.run_simulation(simulation.id)
        return Response(SimulationSerializer(simulation).data, status=status.HTTP_201_CREATED)


class SimulationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SimulationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Simulation.objects.filter(user=self.request.user)
        else:
            session_simulation_id = self.request.session.get('last_simulation_id')
            if session_simulation_id:
                return Simulation.objects.filter(id=session_simulation_id, user__isnull=True)
            return Simulation.objects.none()


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
    permission_classes = [AllowAny]

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
                elif file_type == 'geometry':
                    file_path = simulation.result.geometry_image.path
                    filename = f'simulation_{pk}_geometry.png'
                    content_type = 'image/png'
                elif file_type == 'mesh':
                    file_path = simulation.result.mesh_image.path
                    filename = f'simulation_{pk}_mesh.png'
                    content_type = 'image/png'
                elif file_type == 'results':
                    file_path = simulation.result.results_image.path
                    filename = f'simulation_{pk}_results.png'
                    content_type = 'image/png'
                elif file_type == 'summary':
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
                    with open(temp_file.name, 'w') as f:
                        json.dump(simulation.result.summary, f, indent=2)

                    file_path = temp_file.name
                    filename = f'simulation_{pk}_summary.json'
                    content_type = 'application/json'
                else:
                    return Response({'detail': 'Invalid file type.'}, status=status.HTTP_400_BAD_REQUEST)

                if os.path.exists(file_path):
                    response = FileResponse(
                        open(file_path, 'rb'),
                        as_attachment=True,
                        filename=filename,
                        content_type=content_type
                    )
                    if file_type == 'summary':
                        os.unlink(file_path)

                    return response
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
                data['has_geometry_image'] = bool(simulation.result.geometry_image)
                data['has_mesh_image'] = bool(simulation.result.mesh_image)
                data['has_results_image'] = bool(simulation.result.results_image)
                data['has_nodal_stress_image'] = bool(simulation.result.nodal_stress_image)
                data['has_displacement_image'] = bool(simulation.result.displacement_image)

                # Добавляем URL для всех изображений
                if simulation.result.geometry_image:
                    data['geometry_image_url'] = request.build_absolute_uri(
                        simulation.result.geometry_image.url)
                if simulation.result.mesh_image:
                    data['mesh_image_url'] = request.build_absolute_uri(
                        simulation.result.mesh_image.url)
                if simulation.result.results_image:
                    data['results_image_url'] = request.build_absolute_uri(
                        simulation.result.results_image.url)
            return Response(data)
        except Simulation.DoesNotExist:
            return Response({'detail': 'Simulation not found.'}, status=status.HTTP_404_NOT_FOUND)

class CancelSimulationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, format=None):
        try:
            simulation = Simulation.objects.get(pk=pk, user=request.user)
        except Simulation.DoesNotExist:
            return Response({'detail': 'Симуляция не найдена.'},
                          status=status.HTTP_404_NOT_FOUND)

        # Проверяем, что симуляция в активном состоянии
        if simulation.status not in ['PENDING', 'RUNNING']:
            return Response({'detail': 'Можно отменить только запущенную или ожидающую симуляцию.'},
                          status=status.HTTP_400_BAD_REQUEST)

        # Обновляем статус
        simulation.status = 'FAILED'
        simulation.save()

        # В реальном приложении здесь также нужно отменить задачу Celery
        # from celery.task.control import revoke
        # revoke(task_id, terminate=True)

        return Response({'detail': 'Симуляция отменена.'}, status=status.HTTP_200_OK)

class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]