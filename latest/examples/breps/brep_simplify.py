import pathlib

from compas_viewer import Viewer

from compas.datastructures import Mesh
from compas.files import OBJ
from compas.geometry import Scale
from compas.geometry import Translation
from compas.tolerance import TOL
from compas_occt.brep import OCCBrep

TOL.lineardeflection = 0.1

# Read the OBJ as 9 separate solids. Mesh.from_obj welds the touching solids into one
# mesh; reading the raw vertices/faces keeps them apart so Mesh.exploded recovers all 9.
obj = OBJ(pathlib.Path(__file__).parent / "merge_test.obj")
obj.read()
mesh = Mesh.from_vertices_and_faces(obj.reader.vertices, obj.reader.faces)
solids = mesh.exploded()
print("separate solids:", len(solids))

# Recenter on the shared centre.
points = [solid.vertex_coordinates(v) for solid in solids for v in solid.vertices()]
center = [(min(p[i] for p in points) + max(p[i] for p in points)) / 2 for i in range(3)]
for solid in solids:
    solid.transform(Translation.from_vector([-c for c in center]))

# Merge each solid's coplanar triangles into flat faces.
breps = []
for solid in solids:
    brep = OCCBrep.from_mesh(solid, solid=False)
    brep.simplify(merge_edges=True, merge_faces=True)
    breps.append(brep)
brep = OCCBrep.from_breps(breps)

print("triangles:", sum(s.number_of_faces() for s in solids), "-> flat brep faces:", len(brep.faces))

# Visualise: triangulated input (left) vs merged flat Brep (right).
viewer = Viewer()

scale = Scale.from_factors([0.001, 0.001, 0.001])
for solid in solids:
    viewer.scene.add(solid.transformed(Translation.from_vector([-1.2, 0, 0]) * scale), show_points=False)
viewer.scene.add(brep.transformed(Translation.from_vector([1.2, 0, 0]) * scale), show_points=False)

viewer.show()
