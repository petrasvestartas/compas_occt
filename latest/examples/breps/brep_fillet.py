from compas_viewer import Viewer

from compas.geometry import Box
from compas_occt.brep import OCCBrep

# Construct a brep and round all of its edges with a constant-radius fillet.

brep = OCCBrep.from_box(Box(2))
brep = brep.filleted(0.3)

# =============================================================================
# Visualization
# =============================================================================

viewer = Viewer()

viewer.renderer.camera.target = [0, 0, 0]
viewer.renderer.camera.position = [3, -5, 2]

viewer.scene.add(brep, linewidth=2, show_points=False)

viewer.show()
