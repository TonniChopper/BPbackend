from django.db import models
import os

# class Simulation(models.Model):
#     name = models.CharField(max_length=100)
#     pressure = models.FloatField()
#     temperature = models.FloatField()
#     result_data = models.TextField(null=True, blank=True)
#     result_image = models.ImageField(upload_to='simulations/', null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     def __str__(self):
#         return self.name

class Graph(models.Model):
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