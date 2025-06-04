import os
import json
import numpy as np
import matplotlib
import logging
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.conf import settings
from django.core.files.base import ContentFile
from .image_capture import ImageCapture
logger = logging.getLogger(__name__)

class ResultProcessor:
    """Class for processing simulation results from MAPDL"""

    @staticmethod
    def process_result(result, simulation_id, parameters=None):
        """Process the simulation result and generate summary statistics."""
        # Create a directory for the results
        result_dir = os.path.join(settings.MEDIA_ROOT, 'simulation_results', str(simulation_id))
        os.makedirs(result_dir, exist_ok=True)

        # Displascement calculations
        displacement_result = result.nodal_displacement(0)

        displacement_norms = []
        for disp in displacement_result:
            if hasattr(disp, '__iter__') and not isinstance(disp, np.ndarray):
                norm = np.sqrt(sum(d * d for d in disp))
            elif isinstance(disp, np.ndarray):
                norm = np.linalg.norm(disp)
            else:
                norm = abs(disp)
            displacement_norms.append(norm)

        displacement_norms_array = np.array(displacement_norms)

        # Statistics
        max_displacement = displacement_norms_array.max()
        min_displacement = displacement_norms_array.min()
        avg_displacement = displacement_norms_array.mean()

        # Stress calculations
        nnum, stress = result.principal_nodal_stress(0)
        von_mises = stress[:, -1]  # von-Mises stress
        von_mises = von_mises[~np.isnan(von_mises)]
        logger.debug(f"Stress array shape: {stress.shape}, non-zero values: {np.count_nonzero(stress)}")
        logger.debug(f"Von Mises range: {stress.min()} to {stress.max()}")

        # Save the result statistics to a text file
        result_file_path = os.path.join(result_dir, 'result.txt')
        with open(result_file_path, 'w') as f:
            f.write(f"Maximum displacement: {max_displacement}\n")
            f.write(f"Maximum stress: {von_mises.max()}\n")
            f.write(f"Minimum displacement: {min_displacement}\n")
            f.write(f"Average displacement: {avg_displacement}\n")
            f.write(f"Average stress: {von_mises.mean()}\n")
            f.write(f"Total nodes: {len(result.mesh.nodes)}\n")
            f.write(f"Total elements: {len(result.mesh.enum)}\n")

            solution_output_path = getattr(result, '_solution_output_path', None)
            if solution_output_path and os.path.exists(solution_output_path):
                f.write("\n\n--- MAPDL SOLUTION OUTPUT ---\n\n")
                try:
                    with open(solution_output_path, 'r') as solve_file:
                        f.write(solve_file.read())
                except Exception as e:
                    f.write(f"Error reading solution output: {str(e)}")

        image_paths = getattr(result, '_image_paths', {})

        # Create summary statistics
        def safe_float(value):
            try:
                float_val = float(value)
                if np.isnan(float_val) or np.isinf(float_val):
                    return 0.0
                return float_val
            except:
                return 0.0

        summary = {
            'max_displacement': safe_float(max_displacement),
            'min_displacement': safe_float(min_displacement),
            'avg_displacement': safe_float(avg_displacement),
            'max_stress': safe_float(von_mises.max()),
            'min_stress': safe_float(von_mises.min()),
            'avg_stress': safe_float(von_mises.mean()),
            'node_count': len(result.mesh.nodes),
            'element_count': len(result.mesh.enum),
            'has_mesh_image': 'mesh_image' in image_paths,
            'has_stress_image': 'stress_image' in image_paths,
            'has_deformation_image': 'deformation_image' in image_paths,
        }

        with open(os.path.join(result_dir, 'summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)

        rel_result_file = os.path.relpath(result_file_path, settings.MEDIA_ROOT)
        rel_mesh_image = os.path.relpath(image_paths.get('mesh_image', ''),
                                         settings.MEDIA_ROOT) if 'mesh_image' in image_paths else None
        rel_stress_image = os.path.relpath(image_paths.get('stress_image', ''),
                                            settings.MEDIA_ROOT) if 'stress_image' in image_paths else None
        rel_deformation_image = os.path.relpath(image_paths.get('deformation_image', ''),
                                            settings.MEDIA_ROOT) if 'deformation_image' in image_paths else None

        return {
            'result_file': rel_result_file,
            'mesh_image': rel_mesh_image,
            'stress_image': rel_stress_image,
            'deformation_image' : rel_deformation_image,
            'summary': summary
        }
