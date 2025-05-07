from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.conf import settings  # Используем ссылку на кастомную модель User
import os


class Simulation(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='simulations',
        null=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    parameters = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def is_active(self):
        return timezone.now() < self.created_at + timedelta(days=2)

    def delete(self, *args, **kwargs):
        if hasattr(self, 'result'):
            self.result.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"Simulation {self.pk} for user {username}"


# class SimulationResult(models.Model):
#     simulation = models.OneToOneField(Simulation, on_delete=models.CASCADE, related_name='result')
#     result_file = models.FileField(upload_to='simulation_results/')
#     stress_image = models.ImageField(upload_to='simulation_images/')
#     texture_image = models.ImageField(upload_to='simulation_images/')
#     temp_image = models.ImageField(upload_to='simulation_images/')
#     stress_model = models.FileField(upload_to='simulation_models/', null=True, blank=True)
#     texture_model = models.FileField(upload_to='simulation_models/', null=True, blank=True)
#     temp_model = models.FileField(upload_to='simulation_models/', null=True, blank=True)
#     summary = models.JSONField()
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"Result for Simulation {self.simulation.pk}"
#
#
#     def delete(self, *args, **kwargs):
#         # Удаляем связанные файлы при удалении результата
#         if self.result_file:
#             if os.path.isfile(self.result_file.path):
#                 os.remove(self.result_file.path)
#         if self.stress_image:
#             if os.path.isfile(self.stress_image.path):
#                 os.remove(self.stress_image.path)
#         if self.texture_image:
#             if os.path.isfile(self.texture_image.path):
#                 os.remove(self.texture_image.path)
#         if self.temp_image:
#             if os.path.isfile(self.temp_image.path):
#                 os.remove(self.temp_image.path)
#         if self.stress_model:
#             if os.path.isfile(self.stress_model.path):
#                 os.remove(self.stress_model.path)
#         if self.texture_model:
#             if os.path.isfile(self.texture_model.path):
#                 os.remove(self.texture_model.path)
#         if self.temp_model:
#             if os.path.isfile(self.temp_model.path):
#                 os.remove(self.temp_model.path)
#         # Удаляем сам объект
#         super().delete(*args, **kwargs)

class SimulationResult(models.Model):
    simulation = models.OneToOneField(Simulation, on_delete=models.CASCADE, related_name='result')
    result_file = models.FileField(upload_to='simulation_results/', null=True)

    # Изображения этапов
    geometry_image = models.ImageField(upload_to='simulation_results/', null=True)
    mesh_image = models.ImageField(upload_to='simulation_results/', null=True)
    results_image = models.ImageField(upload_to='simulation_results/', null=True)

    # Существующие поля
    nodal_stress_image = models.ImageField(upload_to='simulation_results/', null=True)
    mesh_image2 = models.ImageField(upload_to='simulation_results/', null=True)
    displacement_image = models.ImageField(upload_to='simulation_results/', null=True)

    nodal_stress_model = models.FileField(upload_to='simulation_results/', null=True)
    mesh_model = models.FileField(upload_to='simulation_results/', null=True)
    displacement_model = models.FileField(upload_to='simulation_results/', null=True)

    summary = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
         return f"Result for Simulation {self.simulation.pk}"
