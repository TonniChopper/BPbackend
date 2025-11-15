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
    """
    Serializer for Simulation model with nested result data

    Includes URLs for result images and summary statistics.
    Validates simulation parameters before saving.
    """
    user = UserSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    has_result = serializers.SerializerMethodField()
    result_summary = serializers.SerializerMethodField()
    mesh_image_url = serializers.SerializerMethodField()
    stress_image_url = serializers.SerializerMethodField()
    deformation_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Simulation
        fields = ['id', 'title', 'user', 'parameters', 'status', 'created_at', 'completed_at',
                  'has_result', 'result_summary', 'mesh_image_url', 'stress_image_url', 'deformation_image_url']

    def validate_parameters(self, value):
        """Validate simulation parameters with detailed error messages"""
        required_fields = {
            'e': 'Young\'s modulus (Pa)',
            'nu': 'Poisson\'s ratio',
            'length': 'Beam length (m)',
            'width': 'Beam width (m)',
            'depth': 'Beam depth (m)',
            'radius': 'Hole radius (m)',
            'num': 'Number of holes',
            'element_size': 'Element size (m)',
            'pressure': 'Applied pressure (Pa)'
        }

        # Check for missing fields
        missing_fields = [field for field in required_fields if field not in value]
        if missing_fields:
            missing_names = [f"{field} ({required_fields[field]})" for field in missing_fields]
            raise serializers.ValidationError(
                f"Missing required parameter(s): {', '.join(missing_names)}"
            )

        # Validate ranges with detailed messages
        errors = []

        if value['e'] <= 0:
            errors.append("Young's modulus (e) must be positive. Typical steel: 2.1e11 Pa")
        if not 0 <= value['nu'] < 0.5:
            errors.append(f"Poisson's ratio (nu) must be between 0 and 0.5. Current: {value['nu']}")
        if value['length'] <= 0:
            errors.append(f"Length must be positive. Current: {value['length']}")
        if value['width'] <= 0:
            errors.append(f"Width must be positive. Current: {value['width']}")
        if value['depth'] <= 0:
            errors.append(f"Depth must be positive. Current: {value['depth']}")
        if value['radius'] <= 0:
            errors.append(f"Radius must be positive. Current: {value['radius']}")
        if value['num'] < 1:
            errors.append(f"Number of holes must be at least 1. Current: {value['num']}")
        if value['element_size'] <= 0:
            errors.append(f"Element size must be positive. Current: {value['element_size']}")

        # Additional validation: radius shouldn't be too large
        if value['radius'] > value['width'] / 2:
            errors.append(f"Radius ({value['radius']}m) is too large for beam width ({value['width']}m)")

        if errors:
            raise serializers.ValidationError(errors)

        return value

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

