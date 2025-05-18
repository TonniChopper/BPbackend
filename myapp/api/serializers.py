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
    mesh_image_url = serializers.SerializerMethodField()
    stress_image_url = serializers.SerializerMethodField()
    deformation_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Simulation
        fields = ['id', 'user', 'parameters', 'status', 'created_at', 'completed_at',
                  'has_result', 'result_summary', 'mesh_image_url', 'stress_image_url','deformation_image_url']

    def get_has_result(self, obj):
        return hasattr(obj, 'result')

    def get_result_summary(self, obj):
        if hasattr(obj, 'result'):
            return obj.result.summary
        return None

    def get_mesh_image_url(self, obj):
        if hasattr(obj, 'result') and obj.result.mesh_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.result.mesh_image.url)
            return obj.result.mesh_image.url
        return None
    def get_stress_image_url(self, obj):
        if hasattr(obj, 'result') and obj.result.stress_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.result.stress_image.url)
            return obj.result.stress_image.url
        return None
    def get_deformation_image_url(self, obj):
        if hasattr(obj, 'result') and obj.result.deformation_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.result.deformation_image.url)
            return obj.result.deformation_image.url
        return None


class SimulationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationResult
        fields = ['id', 'simulation', 'result_file', 'mesh_image', 'stress_image','deformation_image',
                 'summary', 'created_at']
        read_only_fields = ['id', 'created_at']

