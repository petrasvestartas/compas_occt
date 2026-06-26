import pathlib

from compas_viewer import Viewer

from compas.datastructures import Mesh
from compas.files import OBJ
from compas.geometry import Scale
from compas.geometry import Translation
from compas.tolerance import TOL
from compas_occt.brep import OCCBrep

TOL.lineardeflection = 0.1


def solids_from_obj(path):
    """Read an OBJ as a list of separate (un-welded) solids.

    The file is an assembly of several solids but has no ``o``/``g`` object tags,
    so ``Mesh.from_obj`` would weld it into a single, partly non-manifold mesh:
    the solids get fused where they touch, which stops OpenCASCADE from merging
    their coplanar faces cleanly. Reading the *raw* vertices and faces with the
    native COMPAS OBJ reader and splitting them into connected components by
    shared vertices keeps every solid intact.
    """
    obj = OBJ(path)
    obj.read()
    vertices = obj.reader.vertices  # raw, un-welded vertex coordinates
    faces = obj.reader.faces  # raw face indices

    # union-find: group faces that share vertices into separate solids
    parent = {}

    def root(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            parent.setdefault(a, a)
            parent[root(a)] = root(b)

    groups = {}
    for face in faces:
        groups.setdefault(root(face[0]), []).append(face)

    meshes = []
    for group in groups.values():
        used = sorted({v for face in group for v in face})
        index = {v: i for i, v in enumerate(used)}
        meshes.append(Mesh.from_vertices_and_faces([vertices[v] for v in used], [[index[v] for v in face] for face in group]))
    return meshes


# the OBJ is an assembly of separate triangulated solids
meshes = solids_from_obj(pathlib.Path(__file__).parent / "merge_test.obj")
print("separate solids:", len(meshes))

# recenter all solids on their shared centre
points = [mesh.vertex_coordinates(v) for mesh in meshes for v in mesh.vertices()]
center = [(min(p[i] for p in points) + max(p[i] for p in points)) / 2 for i in range(3)]
for mesh in meshes:
    mesh.transform(Translation.from_vector([-c for c in center]))

# merge the coplanar triangles of each solid into flat faces with OpenCASCADE's
# ShapeUpgrade_UnifySameDomain (exposed as OCCBrep.simplify)
breps = []
for mesh in meshes:
    brep = OCCBrep.from_mesh(mesh, solid=False)
    brep.simplify(merge_edges=True, merge_faces=True)
    breps.append(brep)
brep = OCCBrep.from_breps(breps)

print("triangles:", sum(m.number_of_faces() for m in meshes), "-> flat brep faces:", len(brep.faces))

# ==============================================================================
# Visualisation: triangulated input (left) vs merged flat Brep (right)
# ==============================================================================

viewer = Viewer()

scale = Scale.from_factors([0.001, 0.001, 0.001])
for mesh in meshes:
    viewer.scene.add(mesh.transformed(Translation.from_vector([-1.2, 0, 0]) * scale), show_points=False)
viewer.scene.add(brep.transformed(Translation.from_vector([1.2, 0, 0]) * scale), show_points=False)

viewer.show()
