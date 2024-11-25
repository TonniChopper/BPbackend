from rest_framework import serializers
from .models import Graph

# class SimulationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Simulation
#         fields = '__all__'

class GraphSerializer(serializers.ModelSerializer):
    class Meta:
        model = Graph
        fields = ['id', 'pressure', 'temperature', 'image', 'created_at']
        extra_kwargs = {
            'image': {'required': False}
        }