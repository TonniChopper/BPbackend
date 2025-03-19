from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.conf import settings  # Используем ссылку на кастомную модель User
import os

class Simulation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='simulations'
    )
    simulation_result = models.FileField(
        upload_to='simulations/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def is_active(self):
        # Returns True if the simulation is less than 2 days old
        return timezone.now() < self.created_at + timedelta(days=2)

    def delete(self, *args, **kwargs):
        if self.simulation_result and self.simulation_result.name:
            file_path = self.simulation_result.path
            if os.path.isfile(file_path):
                os.remove(file_path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Simulation {self.pk} for user {self.user.username}"