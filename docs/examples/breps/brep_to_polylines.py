from compas_viewer import Viewer

from compas.colors import Color
from compas.geometry import Point
from compas.geometry import Polyhedron
from compas.geometry import Polyline
from compas.geometry import centroid_points
from compas_occt.brep import OCCBrep

# A dodecahedron: twelve pentagonal faces, every one of them a flat polygon.
brep = OCCBrep.from_mesh(Polyhedron.from_platonicsolid(12).to_mesh(), solid=True)

assert brep.is_polygonal

# So it reduces to one closed polyline per face loop, and nothing is lost.
polylines = brep.to_polylines()


def shrink(polyline: Polyline, factor: float = 0.75) -> Polyline:
    """Pull the points of a closed polyline in towards its own centre."""
    centre = Point(*centroid_points(polyline.points[:-1]))
    return Polyline([centre + (point - centre) * factor for point in polyline.points])


# Shrinking each one about its own centre pulls the twelve faces apart, so that
# what the boundary of a single face looks like becomes visible.
faces = [shrink(polyline) for polyline in polylines]

# =============================================================================
# Visualization
# =============================================================================

viewer = Viewer()

viewer.renderer.camera.target = [0, 0, 0]
viewer.renderer.camera.position = [4, -6, 3]

viewer.scene.add(brep, opacity=0.3, show_points=False, linewidth=1, linecolor=Color(0.7, 0.7, 0.7))

for polyline in faces:
    viewer.scene.add(polyline, linewidth=4, linecolor=Color.red(), show_points=False)

viewer.show()
