from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.conf import settings
import hashlib
import json


class Simulation(models.Model):
    """
    Model representing a MAPDL simulation

    Stores simulation parameters, status, and metadata.
    Uses SHA-256 hash for caching identical simulations.
    """
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
    parameters_hash = models.CharField(
        max_length=128,
        db_index=True,
        null=True,
        blank=True,
        help_text='SHA-256 hash of parameters for caching'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def is_active(self):
        return timezone.now() < self.created_at + timedelta(days=2)

    def save(self, *args, **kwargs):
        # Generate parameters hash when saving (SHA-256)
        if self.parameters:
            params_str = json.dumps(self.parameters, sort_keys=True)
            self.parameters_hash = hashlib.sha256(params_str.encode()).hexdigest()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if hasattr(self, 'result'):
            self.result.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"Simulation {self.pk} for user {username}"

class SimulationResult(models.Model):
    """
    Model storing simulation results and generated images

    Contains result files, visualization images (mesh, stress, deformation),
    and summary statistics in JSON format.
    """
    simulation = models.OneToOneField(
        Simulation,
        on_delete=models.CASCADE,
        related_name='result'
    )
    result_file = models.FileField(
        upload_to='simulation_results/',
        null=True,
        help_text='Text file with complete simulation results'
    )
    mesh_image = models.ImageField(
        upload_to='simulation_results/',
        null=True,
        help_text='Mesh visualization image'
    )
    stress_image = models.ImageField(
        upload_to='simulation_results/',
        null=True,
        help_text='Stress distribution (von Mises) image'
    )
    deformation_image = models.ImageField(
        upload_to='simulation_results/',
        null=True,
        help_text='Deformation visualization image'
    )
    summary = models.JSONField(
        default=dict,
        help_text='Summary statistics (max/min/avg stress and displacement)'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result for Simulation {self.simulation.pk}"
