from django.db import models
from django.conf import settings  # Используем ссылку на кастомную модель User
import os

class Graph(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    pressure = models.FloatField()
    temperature = models.FloatField()
    image = models.ImageField(upload_to='simulations/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    simulation_id = models.IntegerField()

    def __str__(self):
        return f"Graph for pressure: {self.pressure}, temperature: {self.temperature}"

    def delete(self, *args, **kwargs):
        if self.image and self.image.name:
            image_path = self.image.path
            if os.path.isfile(image_path):
                os.remove(image_path)
        super().delete(*args, **kwargs)
