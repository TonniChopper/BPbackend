import os
import json
import tempfile
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from redis import Redis
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import FileResponse
from rest_framework.views import APIView

from backend import settings
from myapp.models import Simulation
from myapp.api.serializers import SimulationSerializer, UserSerializer
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
            # Queue async task instead of synchronous execution
            SimulationService.queue_simulation(simulation.id)
            return Response({'detail': 'Simulation resumed.'}, status=status.HTTP_200_OK)
        except Simulation.DoesNotExist:
            return Response({'detail': 'Simulation not found.'}, status=status.HTTP_404_NOT_FOUND)


class SimulationDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, file_type):
        file_path = None
        try:
            if request.user.is_authenticated:
                simulation = Simulation.objects.get(pk=pk, user=request.user)
            else:
                session_simulation_id = request.session.get('last_simulation_id')
                if session_simulation_id and str(pk) == str(session_simulation_id):
                    simulation = Simulation.objects.get(pk=pk, user__isnull=True)
                else:
                    return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
            if simulation.status != 'COMPLETED':
                return Response({'detail': 'Simulation results not ready.'}, status=status.HTTP_400_BAD_REQUEST)

            if not hasattr(simulation, 'result'):
                return Response({'detail': 'No results found for this simulation.'}, status=status.HTTP_404_NOT_FOUND)

            try:
                if file_type == 'result':
                    file_path = simulation.result.result_file.path
                    filename = f'simulation_{pk}_result.txt'
                    content_type = 'text/plain'
                elif file_type == 'mesh':
                    file_path = simulation.result.mesh_image.path
                    filename = f'simulation_{pk}_mesh.png'
                    content_type = 'image/png'
                elif file_type == 'stress':
                    file_path = simulation.result.stress_image.path
                    filename = f'simulation_{pk}_stress.png'
                    content_type = 'image/png'
                elif file_type == 'deformation':
                    file_path = simulation.result.deformation_image.path
                    filename = f'simulation_{pk}_deform.png'
                    content_type = 'image/png'
                elif file_type == 'summary':
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
                        json.dump(simulation.result.summary, temp_file, indent=2)
                        file_path = temp_file.name
                    filename = f'simulation_{pk}_summary.json'
                    content_type = 'application/json'
                else:
                    return Response({'detail': 'Invalid file type.'}, status=status.HTTP_400_BAD_REQUEST)

                if file_path and os.path.exists(file_path):
                    response = FileResponse(
                        open(file_path, 'rb'),
                        as_attachment=True,
                        filename=filename,
                        content_type=content_type
                    )
                    if file_type == 'summary':
                        # Cleanup temporary file after sending
                        try:
                            os.unlink(file_path)
                        except OSError:
                            pass

                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    return response
                else:
                    return Response({'detail': 'File not found on server.'}, status=status.HTTP_404_NOT_FOUND)
            except (AttributeError, ValueError) as e:
                return Response({'detail': f'Error accessing file: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            return Response({'detail': 'Simulation not found.'},
                          status=status.HTTP_404_NOT_FOUND)

        if simulation.status not in ['PENDING', 'RUNNING']:
            return Response({'detail': 'Only pending or running simulations can be canceled.'},
                          status=status.HTTP_400_BAD_REQUEST)

        # Get task_id from Redis
        try:
            redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
            task_id = redis_client.get(f"simulation_task_id:{pk}")

            if task_id:
                task_id = task_id.decode('utf-8')
                # Cancel the Celery task
                from celery import current_app
                current_app.control.revoke(task_id, terminate=True, signal='SIGKILL')
                logger.info(f"Cancelled Celery task {task_id} for simulation {pk}")
        except Exception as e:
            logger.error(f"Error cancelling task: {e}")

        simulation.status = 'FAILED'
        simulation.save()


        return Response({'detail': 'Simulation canceled.'}, status=status.HTTP_200_OK)

class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class HealthCheckView(APIView):
    """Health check endpoint for monitoring system status"""
    permission_classes = [AllowAny]

    def get(self, request):
        from django.db import connection

        try:
            # Check database connection
            connection.ensure_connection()
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        # Check Redis connection
        try:
            redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
            redis_client.ping()
            redis_status = "healthy"
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"

        # Overall status
        status_code = status.HTTP_200_OK if db_status == "healthy" and redis_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

        return Response({
            'status': 'healthy' if status_code == 200 else 'unhealthy',
            'database': db_status,
            'redis': redis_status,
            'timestamp': timezone.now().isoformat()
        }, status=status_code)


class SimulationStatisticsView(APIView):
    """Get user's simulation statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Count, Avg, Q

        user_simulations = Simulation.objects.filter(user=request.user)

        # Calculate statistics
        total = user_simulations.count()
        by_status = user_simulations.values('status').annotate(count=Count('status'))

        # Calculate average completion time for completed simulations
        completed = user_simulations.filter(status='COMPLETED', completed_at__isnull=False)
        avg_time = None
        if completed.exists():
            from django.db.models import F, ExpressionWrapper, DurationField
            avg_duration = completed.annotate(
                duration=ExpressionWrapper(
                    F('completed_at') - F('created_at'),
                    output_field=DurationField()
                )
            ).aggregate(avg=Avg('duration'))['avg']
            if avg_duration:
                avg_time = avg_duration.total_seconds()

        # Recent simulations (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_count = user_simulations.filter(created_at__gte=seven_days_ago).count()

        return Response({
            'total_simulations': total,
            'by_status': {item['status']: item['count'] for item in by_status},
            'average_completion_time_seconds': avg_time,
            'recent_simulations_7_days': recent_count,
        })


class BatchDeleteSimulationsView(APIView):
    """Batch delete multiple simulations"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        simulation_ids = request.data.get('simulation_ids', [])

        if not isinstance(simulation_ids, list) or not simulation_ids:
            return Response(
                {'detail': 'simulation_ids must be a non-empty list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get simulations belonging to user
        simulations = Simulation.objects.filter(
            id__in=simulation_ids,
            user=request.user
        )

        deleted_count = simulations.count()

        if deleted_count == 0:
            return Response(
                {'detail': 'No simulations found or you do not have permission'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Delete with transaction
        with transaction.atomic():
            for simulation in simulations:
                if hasattr(simulation, 'result'):
                    # Delete files
                    for field_name in ['mesh_image', 'stress_image', 'deformation_image', 'result_file']:
                        file_field = getattr(simulation.result, field_name, None)
                        if file_field and hasattr(file_field, 'path'):
                            try:
                                if os.path.exists(file_field.path):
                                    os.remove(file_field.path)
                            except OSError as e:
                                logger.error(f"Failed to delete file {file_field.path}: {e}")

                    simulation.result.delete()
                simulation.delete()

        return Response({
            'detail': f'Successfully deleted {deleted_count} simulation(s)',
            'deleted_count': deleted_count
        })
