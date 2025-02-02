from django.db import models
from django.contrib.auth.models import User
import os

class Graph(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Add this line
    pressure = models.FloatField()
    temperature = models.FloatField()
    image = models.ImageField(upload_to='simulations/')
    created_at = models.DateTimeField(auto_now_add=True)
    simulation_id = models.IntegerField()

    def __str__(self):
        return f"Graph for pressure: {self.pressure}, temperature: {self.temperature}"

    def delete(self, *args, **kwargs):
        if os.path.isfile(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)