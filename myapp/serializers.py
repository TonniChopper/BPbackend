from rest_framework import serializers
from .models import Simulation
from django.contrib.auth.models import User

class SimulationSerializer(serializers.ModelSerializer):
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Simulation
        fields = ['id', 'user', 'parameters', 'simulation_result', 'created_at', 'is_active']
        extra_kwargs = {
            'user': {'read_only': True},
            'simulation_result': {'required': False}
        }

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user