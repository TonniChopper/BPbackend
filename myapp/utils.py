from ansys.mapdl.core import launch_mapdl
import logging

logger = logging.getLogger(__name__)

def run_simulation(length=5, width=2.5, depth=0.1, radius=0.5, num=3, e=2e11, nu=0.27, pressure=1000):
    try:
        mapdl = launch_mapdl()
        # Clear previous session and enter preprocessor
        mapdl.clear()
        mapdl.prep7()

        # Create a block
        mapdl.block(0, length, 0, width, 0, depth)

        # Create cylinders along the block
        for i in range(1, num + 1):
            mapdl.cyl4(i * length / (num + 1), width / 2, radius, '', '', '', 2 * depth)

        # Visualize the block and cylinders
        mapdl.vsbv(1, 'all')
        mapdl.vplot('all')

        # Set mesh size for all areas
        mapdl.lesize("ALL", 0.15, layer1=1)

        # Define material properties (Young\'s modulus and Poisson\'s ratio)
        mapdl.mp('ex', 1, e)
        mapdl.mp('nuxy', 1, nu)

        # Define element type, shape, disable automatic mesh key, and mesh the geometry
        mapdl.et(1, 'SOLID186')
        mapdl.mshape(1, "3D")
        mapdl.mshkey(0)
        mapdl.vmesh('all')
        mapdl.eplot()

        # Apply boundary conditions: fix the face at x=0
        mapdl.nsel('s', 'loc', 'x', 0)
        mapdl.d('all', 'all', 0)

        # Apply pressure boundary condition at x=length
        mapdl.nsel('s', 'loc', 'x', length)
        mapdl.sf('all', 'pres', pressure)

        # Select all entities and finish preprocessor
        mapdl.allsel()
        mapdl.finish()

        # Enter solution processor and solve
        mapdl.slashsolu()
        mapdl.solve()
        mapdl.finish()

        # Re-enter solution processor to get output
        mapdl.slashsolu()
        output = mapdl.solve()
        print(output)

        # Plot principal nodal stresses with specified plot options
        result = mapdl.result
        result.plot_principal_nodal_stress(0, 'seqv', background='w', show_edges=True, text_color='k', add_text=True)

        # Exit MAPDL session
        mapdl.exit()
    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        raise e