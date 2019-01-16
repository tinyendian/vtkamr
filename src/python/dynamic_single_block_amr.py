import numpy as np
import vtk
from vtk.util import numpy_support as nps
import random

class gridPatch:
    """
    Class for specifying a 2D grid patch and creating a vtkUniformGrid
    object for the patch
    """

    # Patch dimensions are the same for all patches
    nx = 16
    ny = 16

    # Refinement ratio is the same for all patches
    refinement_ratio = 2

    def __init__(self, id, level, dx0, dy0, origin):

        # Patch ID
        self.id = id

        # Refinement level
        self.level = level

        # Cell sizes
        self.dx = dx0/float(self.refinement_ratio**level)
        self.dy = dy0/float(self.refinement_ratio**level)

        # Patch coordinate origin in 2D VTK "world coordinates"
        self.origin = origin

        # Generate some fake data by filling the patch with its ID number
        self.data = np.full((self.nx,self.ny), self.id, dtype=np.float64)

    def getVTKGrid(self):
        """
        Return a vtkUniformGrid object for given patch specification
        """

        # Create VTK grid patch
        grid = vtk.vtkUniformGrid()
        grid.SetSpacing(self.dx, self.dy, 0)
        grid.SetExtent(0, self.nx, 0, self.ny, 0, 0)
        grid.SetOrigin([self.origin[0], self.origin[1], 0])

        # Attach data array - note that this can be easily replaced with a pointer
        # into a large data array
        vtkData = nps.numpy_to_vtk(self.data.flat, deep=False, array_type=vtk.VTK_DOUBLE)
        vtkData.SetName('data')
        grid.GetCellData().AddArray(vtkData)

        return grid

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def getAMRGrid(gridPatches):
    """
    Turns a list of gridPatch objects into a vtkNonOverlappingAMR grid object. Note that
    the number of refinement levels and patches per level need to be set at initialisation
    time, so that vtkNonOverlappingAMR needs to be recreated in every time step.
    """

    # Work out refinement levels in the current list of patches, assume that
    # there is only one patch ("block" in VTK) per level
    nlevels = len(gridPatches)
    numBlocksPerLevel = np.full(nlevels, 1)

    grid = vtk.vtkNonOverlappingAMR()
    grid.Initialize(nlevels, numBlocksPerLevel)

    for patch in gridPatches:
        grid.SetDataSet(patch.level, 0, patch.getVTKGrid())

    return grid

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def writeAMRGrid(filename, grid):
    """
    Write AMR grid to a set of VTK files in XML format
    """
    writer = vtk.vtkXMLUniformGridAMRWriter()
    writer.SetFileName(filename)
    writer.SetInputData(grid)
    writer.Update()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def main():

    # Cell widths at base (coarsest) level
    dx0 = 1.0
    dy0 = 1.0

    # Number of time steps
    ntimesteps = 20

    # Maximum refinement level
    max_level = 5

    # This list holds grid patches. VTK AMR container objects are not dynamic - the number
    # of levels and patches (or "blocks" in VTK) need to be set at grid initialisation.
    # However, we could always hold on to the vtkUniformGrid objects for patches that remain
    # over several timesteps, and just recreated the vtkNonOverlappingAMR container object -
    # this should not be expensive.
    patches = []

    # Create base grid at level 0
    current_level = 0
    patches.append(gridPatch(0, current_level, dx0, dy0, [0,0]))

    # Get vtkNonOverlappingAMR object and write VTK file
    grid = getAMRGrid(patches)
    writeAMRGrid("amr_0.vtm", grid)

    # Initialise random number generator for fake dynamic AMR
    random.seed(123)

    for timestep in range(0, ntimesteps):

        print("Timestep: %i" % timestep)

        action = random.random()

        # Refine grid?
        if action > 0.2 and current_level < max_level:

            current_level += 1

            # Compute position of new patch, placing it at random position inside the parent patch
            nx = patches[-1].nx
            ny = patches[-1].ny
            origin = patches[-1].origin
            dx = patches[-1].dx
            dy = patches[-1].dy
            new_origin = [origin[0] + random.randint(0,int(nx/2))*dx,
                          origin[1] + random.randint(0,int(ny/2))*dy]

            print("Adding patch at level %i" % current_level)
            patches.append(gridPatch(patches[-1].id+1, current_level, dx0, dy0, new_origin))

        # Remove patch?
        elif action > 0.1 and current_level > 0:
            print("Removing patch at level %i" % current_level)
            current_level -= 1
            del patches[-1]

        grid = getAMRGrid(patches)
        print("Number of levels: %i" % grid.GetNumberOfLevels())
        print("")
        writeAMRGrid("amr_%i.vtm" % (timestep+1), grid)

if __name__ == '__main__':
    main()
