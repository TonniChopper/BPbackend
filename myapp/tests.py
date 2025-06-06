import unittest
from unittest.mock import MagicMock, patch
import os
from django.conf import settings
from django.test import TestCase

from myapp.services.mapdl_handler import MAPDLHandler
from myapp.models import Simulation


class MAPDLHandlerTests(TestCase):
    def setUp(self):
        # Create test directory
        self.test_dir = os.path.join(settings.MEDIA_ROOT, 'test_simulation')
        os.makedirs(self.test_dir, exist_ok=True)

        # Sample parameters for simulation
        self.test_parameters = {
            'id': 'test123',
            'e': 2.1e11,
            'nu': 0.3,
            'length': 5,
            'width': 2.5,
            'depth': 0.1,
            'radius': 0.5,
            'num': 3,
            'element_size': 0.125,
            'pressure': 1000
        }

    @patch('myapp.services.mapdl_handler.launch_mapdl')
    def test_get_mapdl(self, mock_launch_mapdl):
        # Setup mock
        mock_mapdl = MagicMock()
        mock_launch_mapdl.return_value = mock_mapdl

        # Test getting MAPDL instance
        handler = MAPDLHandler()
        mapdl = handler.get_mapdl()

        # Assertions
        self.assertEqual(mapdl, mock_mapdl)
        mock_launch_mapdl.assert_called_once()

        # Test singleton behavior
        mapdl2 = handler.get_mapdl()
        self.assertEqual(mapdl, mapdl2)
        mock_launch_mapdl.assert_called_once()  # Should not be called again

    @patch('myapp.services.mapdl_handler.launch_mapdl')
    def test_run_simulation(self, mock_launch_mapdl):
        # Setup mocks
        mock_mapdl = MagicMock()
        mock_result = MagicMock()
        mock_solve_output = MagicMock()

        # Setup stress results
        stress_array = MagicMock()
        stress_array.__getitem__.return_value = MagicMock()
        stress_array.min.return_value = 10.0
        stress_array.max.return_value = 100.0

        mock_mapdl.solve.return_value = mock_solve_output
        mock_mapdl.result = mock_result
        mock_launch_mapdl.return_value = mock_mapdl

        # Mock principal_nodal_stress to return stress data
        mock_result.principal_nodal_stress.return_value = (None, stress_array)

        # Set up image capture mock
        with patch('myapp.services.mapdl_handler.ImageCapture.save_simulation_images') as mock_save_images:
            mock_save_images.return_value = {
                'mesh_image': '/path/to/mesh.png',
                'stress_image': '/path/to/stress.png',
                'deformation_image': '/path/to/deform.png'
            }

            # Run test
            handler = MAPDLHandler()
            result = handler.run_simulation(self.test_parameters)

            # Assertions
            self.assertEqual(result, mock_result)
            mock_mapdl.clear.assert_called_once()
            mock_mapdl.prep7.assert_called_once()
            mock_mapdl.solve.assert_called_once()
            mock_save_images.assert_called_once()

            # Check that von Mises stress values were accessed
            mock_result.principal_nodal_stress.assert_called_once()

    @patch('myapp.services.mapdl_handler.launch_mapdl')
    def test_close_mapdl(self, mock_launch_mapdl):
        # Setup mock
        mock_mapdl = MagicMock()
        mock_launch_mapdl.return_value = mock_mapdl

        # Get MAPDL and then close it
        handler = MAPDLHandler()
        handler.get_mapdl()
        handler.close_mapdl()

        # Assertions
        mock_mapdl.exit.assert_called_once()
        self.assertIsNone(handler._mapdl)


class SimulationModelTests(TestCase):
    def test_parameters_hash_generation(self):
        # Create simulation with parameters
        params = {
            'e': 2.1e11,
            'nu': 0.3,
            'length': 5
        }

        simulation = Simulation(title="Test Simulation", parameters=params)
        simulation.save()

        # Check that hash was generated
        self.assertIsNotNone(simulation.parameters_hash)

        # Create another simulation with same parameters
        simulation2 = Simulation(title="Test Simulation 2", parameters=params)
        simulation2.save()

        # Check that hashes match
        self.assertEqual(simulation.parameters_hash, simulation2.parameters_hash)


if __name__ == '__main__':
    unittest.main()