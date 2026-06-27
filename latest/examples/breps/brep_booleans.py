from compas_viewer import Viewer

from compas.geometry import Box
from compas.geometry import Cylinder
from compas.geometry import Frame
from compas.tolerance import TOL

TOL.lineardeflection = 0.1

# Three box/cylinder pairs, one per boolean operation, spaced along the X axis.
boxes = [Box(2, frame=Frame([x, 0, 0])).to_brep() for x in (-3, 0, 3)]
cylinders = [Cylinder(0.7, 3, frame=Frame([x, 0, 0])).to_brep() for x in (-3, 0, 3)]

union = boxes[0] + cylinders[0]
difference = boxes[1] - cylinders[1]
intersection = boxes[2] & cylinders[2]

# ==============================================================================
# Visualisation
# ==============================================================================

viewer = Viewer()

viewer.renderer.camera.target = [0, 0, 0]
viewer.renderer.camera.position = [1, -11, 6]

viewer.scene.add(union, name="union")
viewer.scene.add(difference, name="difference")
viewer.scene.add(intersection, name="intersection")

viewer.show()
