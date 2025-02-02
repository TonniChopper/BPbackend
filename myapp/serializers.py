from rest_framework import serializers
from .models import Graph

class GraphSerializer(serializers.ModelSerializer):
    class Meta:
        model = Graph
        fields = ['id', 'user', 'pressure', 'temperature', 'image', 'created_at', 'simulation_id']
        extra_kwargs = {
            'image': {'required': False}
        }