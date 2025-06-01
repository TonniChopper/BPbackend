import os
import json
import tempfile
from django.shortcuts import render
from redis import Redis
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import FileResponse
from rest_framework.views import APIView

from backend import settings
from myapp.models import Simulation
from myapp.api.serializers import SimulationSerializer, SimulationResultSerializer, UserSerializer
from myapp.tasks.simulation_task import run_simulation_task_with_redis
from myapp.services.simulation_service import SimulationService, logger
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
            simulation = serializer.save(user=None, status='PENDING')
            self.request.session['last_simulation_id'] = simulation.id
            self.request.session.set_expiry(86400)

        # SimulationService.run_simulation(simulation.id)
        task_id = SimulationService.queue_simulation(simulation.id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Add task_id and status to the response
        response_data = serializer.data
        simulation_id = response_data['id']
        task_id = None

        # Get task_id from Redis
        try:
            redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
            task_id = redis_client.get(f"simulation_task_id:{simulation_id}")
            if task_id:
                task_id = task_id.decode('utf-8')
        except Exception as e:
            logger.error(f"Error getting task_id: {e}")

        response_data.update({
            'task_id': task_id,
            'status': 'PENDING',
            'message': 'Simulation queued successfully'
        })

        return Response(response_data, status=status.HTTP_202_ACCEPTED, headers=headers)


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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class SimulationResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            simulation = Simulation.objects.get(pk=pk, user=request.user)
            # if simulation.status not in ['FAILED', 'COMPLETED']:
            #     return Response({'detail': 'Simulation cannot be resumed.'}, status=status.HTTP_400_BAD_REQUEST)
            simulation.status = 'PENDING'
            simulation.save()
            # Запускаем асинхронную задачу вместо синхронного вызова
            SimulationService.queue_simulation(simulation.id)
            return Response({'detail': 'Simulation resumed.'}, status=status.HTTP_200_OK)
        except Simulation.DoesNotExist:
            return Response({'detail': 'Simulation not found.'}, status=status.HTTP_404_NOT_FOUND)


class SimulationDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, file_type):
        global file
        try:
            if request.user.is_authenticated:
                simulation = Simulation.objects.get(pk=pk, user=request.user)
            else:
                session_simulation_id = request.session.get('last_simulation_id')
                if session_simulation_id and str(pk) == str(session_simulation_id):
                    simulation = Simulation.objects.get(pk=pk, user__isnull=True)
                else:
                    return Response({'detail': 'Access denied'},
                                    status=status.HTTP_403_FORBIDDEN)
            if simulation.status != 'COMPLETED':
                return Response({'detail': 'Simulation results not ready.'}, status=status.HTTP_400_BAD_REQUEST)

            if not hasattr(simulation, 'result'):
                return Response({'detail': 'No results found for this simulation.'}, status=status.HTTP_404_NOT_FOUND)

            try:
                if file_type == 'result':
                    file = simulation.result.result_file
                    filename = f'simulation_{pk}_result.txt'
                    content_type = 'text/plain'
                elif file_type == 'mesh':
                    file = simulation.result.mesh_image
                    filename = f'simulation_{pk}_mesh.png'
                    content_type = 'image/png'
                elif file_type == 'stress':
                    file = simulation.result.stress_image
                    filename = f'simulation_{pk}_stress.png'
                    content_type = 'image/png'
                elif file_type == 'deformation':
                    file = simulation.result.deformation_image
                    filename = f'simulation_{pk}_deform.png'
                    content_type = 'image/png'
                elif file_type == 'summary':
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
                    with open(temp_file.name, 'w') as f:
                        json.dump(simulation.result.summary, f, indent=2)

                    file = temp_file.name
                    filename = f'simulation_{pk}_summary.json'
                    content_type = 'application/json'
                else:
                    return Response({'detail': 'Invalid file type.'}, status=status.HTTP_400_BAD_REQUEST)

                if os.path.exists(file.path):
                    response = FileResponse(
                        open(file.path, 'rb'),
                        as_attachment=True,
                        filename=filename,
                        content_type=content_type
                    )
                    if file_type == 'summary':
                        os.unlink(file.path)

                    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file.path)}"'
                    return response
                else:
                    return Response({'detail': 'File not found on server.'}, status=status.HTTP_404_NOT_FOUND)
            except (AttributeError, ValueError) as e:
                return Response({'detail': f'Error accessing file: {str(e)}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Simulation.DoesNotExist:
            return Response({'detail': 'Simulation not found.'}, status=status.HTTP_404_NOT_FOUND)


class DeleteSimulationView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Simulation.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        if hasattr(instance, 'result'):
            if instance.result.mesh_image:
                if os.path.exists(instance.result.mesh_image.path):
                    os.remove(instance.result.mesh_image.path)
            if instance.result.stress_image:
                if os.path.exists(instance.result.stress_image.path):
                    os.remove(instance.result.stress_image.path)
            if instance.result.deformation_image:
                if os.path.exists(instance.result.deformation_image.path):
                    os.remove(instance.result.deformation_image.path)
            instance.result.delete()
        instance.delete()

class SimulationStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            if request.user.is_authenticated:
                simulation = Simulation.objects.get(pk=pk, user=request.user)
            else:
                session_simulation_id = request.session.get('last_simulation_id')
                if session_simulation_id and str(pk) == str(session_simulation_id):
                    simulation = Simulation.objects.get(pk=pk, user__isnull=True)
                else:
                    return Response({'detail': 'Access denied'},
                                    status=status.HTTP_403_FORBIDDEN)

            data = {
                'id': simulation.id,
                'title': simulation.title,
                'status': simulation.status,
                'created_at': simulation.created_at,
                'completed_at': simulation.completed_at,
                'parameters': simulation.parameters,
            }

            if simulation.status == 'COMPLETED' and hasattr(simulation, 'result'):
                # Add result information to the response
                data['result_summary'] = simulation.result.summary
                data['has_mesh_image'] = bool(simulation.result.mesh_image)
                data['has_stress_image'] = bool(simulation.result.stress_image)
                data['has_deformation_image'] = bool(simulation.result.deformation_image)

                if simulation.result.mesh_image:
                    data['mesh_image_url'] = request.build_absolute_uri(
                        simulation.result.mesh_image.url)
                if simulation.result.stress_image:
                    data['stress_image_url'] = request.build_absolute_uri(
                        simulation.result.stress_image.url)
                if simulation.result.deformation_image:
                    data['deformation_image_url'] = request.build_absolute_uri(
                        simulation.result.deformation_image.url)
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