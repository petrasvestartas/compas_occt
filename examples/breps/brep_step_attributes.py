import os
import tempfile

from compas_viewer import Viewer

from compas.geometry import Box
from compas.tolerance import TOL
from compas_occt.brep import OCCBrep

TOL.lineardeflection = 0.1

# Write a Brep to STEP together with a name and user-defined attributes. The attributes
# are stored as `general_property` entities (cf. OCCT PR #634) so that other CAD systems
# can read them back: strings, integers, and reals are each supported.
brep = OCCBrep.from_box(Box(2))

filepath = os.path.join(tempfile.gettempdir(), "box_with_attributes.step")
brep.to_step_with_attributes(
    filepath,
    name="MyBox",
    attributes={"material": "steel", "count": 3, "thickness": 1.5},
)

# Read the file back: every top-level shape comes with its name and its attributes.
result = OCCBrep.from_step_with_attributes(filepath)
for shape, name, attributes in result:
    print(name, attributes)

# ==============================================================================
# Visualisation
# ==============================================================================

viewer = Viewer()

viewer.renderer.camera.target = [0, 0, 0]
viewer.renderer.camera.position = [5, -8, 4]

shape, name, attributes = result[0]
viewer.scene.add(shape, name=name)

viewer.show()
