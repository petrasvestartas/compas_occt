"""Mesh conversions between COMPAS and the OCC backend.

These build OCC faces/shells, so they require the compiled ``_meshing`` extension. They
return :class:`Shape` handle wrappers (faces/shells), matching ``compas_occ``'s roles of
``triangle_to_face``/``quad_to_face``/``ngon_to_face``/``compas_*_to_occ_shell``.
"""

from typing import Annotated
from typing import Union

import compas.geometry
from compas.datastructures import Mesh
from compas.geometry import Polygon

Triangle = Union[Polygon, Annotated[list[Union[Annotated[list[float], 3], compas.geometry.Point]], 3]]
Quad = Union[Polygon, Annotated[list[Union[Annotated[list[float], 3], compas.geometry.Point]], 4]]
NGon = Union[Polygon, list[Union[Annotated[list[float], 3], compas.geometry.Point]]]


def _coords(points) -> list[list[float]]:
    return [[float(p[0]), float(p[1]), float(p[2])] for p in points]


def triangle_to_face(triangle: Triangle):
    """Convert a triangle (3 points) to a BRep face (``Shape``).

    Raises
    ------
    ValueError
        If the number of points is not 3.

    """
    if len(triangle) != 3:
        raise ValueError("The number of input points should be three.")
    from compas_occt import _occt as _meshing

    return _meshing.triangle_to_face(_coords(triangle))


def quad_to_face(quad: Quad):
    """Convert a quad (4 points) to a BRep face with a ruled surface (``Shape``).

    Raises
    ------
    ValueError
        If the number of points is not 4.

    """
    if len(quad) != 4:
        raise ValueError("The number of input points should be four.")
    from compas_occt import _occt as _meshing

    return _meshing.quad_to_face(_coords(quad))


def ngon_to_face(ngon: NGon):
    """Convert an ngon to a BRep face with a best-fit surface (``Shape``)."""
    from compas_occt import _occt as _meshing

    return _meshing.ngon_to_face(_coords(ngon))


def compas_trimesh_to_occ_shell(mesh: Mesh):
    """Convert a COMPAS triangle mesh to an OCC shell (``Shape``).

    Raises
    ------
    ValueError
        If the mesh is not a triangle mesh.

    """
    if not mesh.is_trimesh():
        raise ValueError("The input mesh is not a triangle mesh.")
    from compas_occt import _occt as _meshing

    faces = [_meshing.triangle_to_face(_coords(mesh.face_coordinates(face))) for face in mesh.faces()]
    return _meshing.shell_from_faces(faces)


def compas_quadmesh_to_occ_shell(mesh: Mesh):
    """Convert a COMPAS quad mesh to an OCC shell (``Shape``).

    Raises
    ------
    ValueError
        If the input mesh is not a quad mesh.

    """
    if not mesh.is_quadmesh():
        raise ValueError("The input mesh is not a quad mesh.")
    from compas_occt import _occt as _meshing

    faces = [_meshing.quad_to_face(_coords(mesh.face_coordinates(face))) for face in mesh.faces()]
    return _meshing.shell_from_faces(faces)


def compas_mesh_to_occ_shell(mesh: Mesh):
    """Convert a general COMPAS mesh to an OCC shell (``Shape``)."""
    from compas_occt import _occt as _meshing

    faces = []
    for face in mesh.faces():
        points = _coords(mesh.face_coordinates(face))
        if len(points) == 3:
            faces.append(_meshing.triangle_to_face(points))
        elif len(points) == 4:
            faces.append(_meshing.quad_to_face(points))
        else:
            faces.append(_meshing.ngon_to_face(points))
    return _meshing.shell_from_faces(faces)
