import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class ImageCapture:
    """Class for capturing images of simulation results and geometry"""

    @staticmethod
    def save_simulation_images(mapdl, result, simulation_id, simulation_dir):
        """Capture and save images of the simulation results and geometry"""
        images = {}

        mesh_path = os.path.join(simulation_dir, 'mesh.png')
        if ImageCapture.capture_mesh(mapdl, mesh_path):
            images['mesh_image'] = mesh_path

        stress_path = os.path.join(simulation_dir, 'stress.png')
        if ImageCapture.capture_stress(result, stress_path):
            images['stress_image'] = stress_path

        deformation_path = os.path.join(simulation_dir, 'deform.png')
        if ImageCapture.capture_deformation(result, deformation_path):
            images['deformation_image'] = deformation_path

        return images

    @staticmethod
    def capture_geometry(mapdl, save_path, window_size=[1920, 1080]):
        """Generate and save an image of the geometry"""
        try:
            # PostProcessing step to ensure the geometry is ready
            mapdl.prep7()

            # Создание и сохранение изображения
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            mapdl.aplot(background='w', show_edges=True, smooth_shading=True,
                        window_size=[1920, 1080], savefig=save_path,
                        off_screen=True)
            plt.close()
            return save_path
        except Exception as e:
            print(f"Failed to create geometry: {e}")
            return None

    @staticmethod
    def capture_mesh(mapdl, save_path, window_size=[1920, 1080]):
        """Generate and save an image of the mesh"""
        try:
            mapdl.prep7()
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            mapdl.eplot(background='w', show_edges=True, smooth_shading=True,
                        window_size=[1920, 1080], savefig=save_path,
                        off_screen=True)
            plt.close()
            return save_path
        except Exception as e:
            print(f"Failed to create mesh: {e}")
            return None

    @staticmethod
    def capture_stress(result, save_path, result_type='stress', window_size=[1920, 1080]):
        """Generate and save an image of the stress results"""
        try:
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            result.plot_principal_nodal_stress(0, 'seqv', background='W', show_edges=True, text_color='k',
                                                   add_text=True,
                                                   window_size=[1920, 1080], screenshot=save_path,
                                                   off_screen=True)
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            plt.close()
            return save_path
        except Exception as e:
            print(f"Failed to create stress image: {e}")
            return None

    @staticmethod
    def capture_deformation(mapdl, save_path, window_size=[1920, 1080]):
        """Generate and save an image of the deformation results"""
        try:
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            mapdl.plot_nodal_displacement(0, 'NORM', background='W', show_edges=True, text_color='k',
                                               add_text=True,
                                               window_size=[1920, 1080], screenshot=save_path,
                                               off_screen=True)
            plt.figure(figsize=(window_size[0] / 100, window_size[1] / 100))
            plt.close()
            return save_path
        except Exception as e:
            print(f"Failed to create deformation image: {e}")
            return None