from compas_viewer import Viewer

from compas.colors import Color
from compas.geometry import Box
from compas.geometry import Brep

A = Box(1).to_brep()

box = Box(1)
box.translate([1, 0.3, 0.5])
B = Brep.from_box(box)

FA, FB = A.overlap(B)  # which faces of A and B overlap
common = A.overlap_intersection(B)  # the common (shared) region between them

# =============================================================================
# Visualization
# =============================================================================

viewer = Viewer()

viewer.renderer.camera.target = [-1, 2, 0]
viewer.renderer.camera.position = [3, -3, 1]

# A and B as wireframes
viewer.scene.add(A, show_faces=False, linewidth=2, show_points=False)
viewer.scene.add(B, show_faces=False, linewidth=2, show_points=False)

# the overlapping faces outlined in red (A) and blue (B)
viewer.scene.add(Brep.from_brepfaces([FA[0]]), show_faces=False, linecolor=Color.red(), linewidth=4, show_points=False)
viewer.scene.add(Brep.from_brepfaces([FB[0]]), show_faces=False, linecolor=Color.blue(), linewidth=4, show_points=False)

# the common intersection between the two surfaces, in green
viewer.scene.add(common, surfacecolor=Color.green(), linecolor=Color.green().darkened(50), linewidth=3, show_points=False)

viewer.show()
