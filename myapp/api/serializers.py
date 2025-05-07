from rest_framework import serializers
from myapp.models import Simulation , SimulationResult
from django.contrib.auth.models import User

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


class SimulationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    has_result = serializers.SerializerMethodField()
    result_summary = serializers.SerializerMethodField()
    geometry_image_url = serializers.SerializerMethodField()
    mesh_image_url = serializers.SerializerMethodField()
    nodal_stress_image_url = serializers.SerializerMethodField()
    displacement_image_url = serializers.SerializerMethodField()
    results_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Simulation
        fields = ['id', 'user', 'parameters', 'status', 'created_at', 'completed_at',
                  'has_result', 'result_summary', 'geometry_image_url', 'mesh_image_url',
                  'nodal_stress_image_url', 'displacement_image_url', 'results_image_url']

    def get_has_result(self, obj):
        return hasattr(obj, 'result')

    def get_result_summary(self, obj):
        if hasattr(obj, 'result'):
            return obj.result.summary
        return None

    def get_geometry_image_url(self, obj):
        if hasattr(obj, 'result') and obj.result.geometry_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.result.geometry_image.url)
            return obj.result.geometry_image.url
        return None

    def get_mesh_image_url(self, obj):
        if hasattr(obj, 'result') and obj.result.mesh_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.result.mesh_image.url)
            return obj.result.mesh_image.url
        return None

    def get_nodal_stress_image_url(self, obj):
        if hasattr(obj, 'result') and obj.result.nodal_stress_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.result.nodal_stress_image.url)
            return obj.result.nodal_stress_image.url
        return None

    def get_displacement_image_url(self, obj):
        if hasattr(obj, 'result') and obj.result.displacement_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.result.displacement_image.url)
            return obj.result.displacement_image.url
        return None

    def get_results_image_url(self, obj):
        if hasattr(obj, 'result') and obj.result.results_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.result.results_image.url)
            return obj.result.results_image.url
        return None


class SimulationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationResult
        fields = ['id', 'simulation', 'result_file',
                 'geometry_image', 'mesh_image', 'results_image',
                 'nodal_stress_image', 'displacement_image',
                 'nodal_stress_model', 'mesh_model', 'displacement_model',
                 'summary', 'created_at']
        read_only_fields = ['id', 'created_at']

