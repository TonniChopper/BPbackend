from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.conf import settings  # Используем ссылку на кастомную модель User
import os
import hashlib
import json


class Simulation(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ]
    title = models.CharField(max_length=255, null=True, blank=True)
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
    parameters_hash = models.CharField(max_length=64,db_index=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def is_active(self):
        return timezone.now() < self.created_at + timedelta(days=2)

    def save(self, *args, **kwargs):
        # Generate parameters hash when saving
        if self.parameters:
            params_str = json.dumps(self.parameters, sort_keys=True)
            self.parameters_hash = hashlib.md5(params_str.encode()).hexdigest()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if hasattr(self, 'result'):
            self.result.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"Simulation {self.pk} for user {username}"

class SimulationResult(models.Model):
    simulation = models.OneToOneField(Simulation, on_delete=models.CASCADE, related_name='result')
    result_file = models.FileField(upload_to='simulation_results/', null=True)

    mesh_image = models.ImageField(upload_to='simulation_results/', null=True)
    stress_image = models.ImageField(upload_to='simulation_results/', null=True)
    deformation_image = models.ImageField(upload_to='simulation_results/', null=True)

    summary = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
         return f"Result for Simulation {self.simulation.pk}"
