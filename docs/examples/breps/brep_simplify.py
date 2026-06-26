import math
import pathlib

from compas_viewer import Viewer

import compas_occt._occt as occt
from compas.datastructures import Mesh
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Scale
from compas.geometry import Translation
from compas.geometry import Vector
from compas.geometry import area_polygon
from compas.geometry import dot_vectors
from compas.geometry import normal_polygon
from compas.geometry import project_point_plane
from compas.tolerance import TOL
from compas_occt.brep import OCCBrep

TOL.lineardeflection = 0.1


def meshes_from_obj(path):
    """Load an OBJ as separate (un-welded) meshes -- one per connected solid."""
    vertices, faces = [], []
    for line in open(path):
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "v":
            vertices.append([float(x) for x in parts[1:4]])
        elif parts[0] == "f":
            faces.append([int(p.split("/")[0]) - 1 for p in parts[1:]])
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for face in faces:
        for i in range(len(face)):
            parent.setdefault(face[i], face[i])
            parent[find(face[i])] = find(face[(i + 1) % len(face)])
    components = {}
    for face in faces:
        components.setdefault(find(face[0]), []).append(face)
    meshes = []
    for component in components.values():
        used = sorted({v for f in component for v in f})
        remap = {v: i for i, v in enumerate(used)}
        meshes.append(Mesh.from_vertices_and_faces([vertices[v] for v in used], [[remap[v] for v in f] for f in component]))
    return meshes


def flat_faces(mesh, angle=2.0):
    """Merge the coplanar faces of a mesh into flat polygon faces, holes included."""
    cos_tol = math.cos(math.radians(angle))
    normals = {face: mesh.face_normal(face) for face in mesh.faces()}

    seen, groups = set(), []
    for start in mesh.faces():
        if start in seen:
            continue
        group, stack, normal = [start], [start], normals[start]
        seen.add(start)
        while stack:
            face = stack.pop()
            for nbr in mesh.face_neighbors(face):
                if nbr not in seen and sum(a * b for a, b in zip(normal, normals[nbr])) >= cos_tol:
                    seen.add(nbr)
                    group.append(nbr)
                    stack.append(nbr)
        groups.append(group)

    faces = []
    for group in groups:
        members = set(group)
        nxt = {u: v for face in group for u, v in mesh.face_halfedges(face) if mesh.halfedge[v].get(u) not in members}
        used, loops = set(), []
        for first in list(nxt):
            if first in used:
                continue
            loop, current = [first], nxt.get(first)
            used.add(first)
            while current is not None and current != first and current not in used:
                loop.append(current)
                used.add(current)
                current = nxt.get(current)
            points = [mesh.vertex_coordinates(v) for v in loop]
            if len(points) >= 3 and area_polygon(points) > 1e-6:
                loops.append(points)
        if not loops:
            continue

        # project every loop onto the region's best-fit plane so the face is exactly planar
        normal = [sum(normals[f][i] for f in group) for i in range(3)]
        length = math.sqrt(sum(x * x for x in normal)) or 1.0
        flat = [p for loop in loops for p in loop]
        origin = [sum(p[i] for p in flat) / len(flat) for i in range(3)]
        region_normal = [x / length for x in normal]
        plane = Plane(Point(*origin), Vector(*region_normal))
        loops = [[list(project_point_plane(Point(*p), plane)) for p in loop] for loop in loops]
        loops.sort(key=area_polygon, reverse=True)  # the largest loop is the outer boundary
        if dot_vectors(normal_polygon(loops[0]), region_normal) < 0:  # keep the face normal outward
            loops = [list(reversed(loop)) for loop in loops]

        face = occt.make_face_polygon(loops[0])
        for hole in loops[1:]:  # cut the inner loops out as holes
            face = occt.face_add_loop(face, occt.shape_explore(occt.make_face_polygon(hole), 5)[0], True)
        faces.append(face)
    return faces


# the OBJ is an assembly of 9 separate solid meshes
meshes = meshes_from_obj(pathlib.Path(__file__).parent / "merge_test.obj")
print("separate meshes:", len(meshes))

# unify the face windings (outward) and recenter on the shared centre
points = [mesh.vertex_coordinates(v) for mesh in meshes for v in mesh.vertices()]
center = [(min(p[i] for p in points) + max(p[i] for p in points)) / 2 for i in range(3)]
for mesh in meshes:
    mesh.unify_cycles()
    mesh.transform(Translation.from_vector([-c for c in center]))

# merge the coplanar faces of every mesh into one Brep of flat faces
faces = [face for mesh in meshes for face in flat_faces(mesh)]
brep = OCCBrep.from_native(occt.compound_from_shapes(faces))
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
