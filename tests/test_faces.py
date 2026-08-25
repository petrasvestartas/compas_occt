"""Faces built from polygons must be planes when the polygon is flat.

A flat polygon has a plane; building it as a fitted surface instead is wrong in
three ways at once. It is slow (an n-sided patch solve, or a ruled surface,
where a wire on a plane would do), it is inexact, and it is invisible to every
downstream planarity test - so callers lose the cheap planar filters that face
comparison and contact detection are built on.

The fitted surface is still correct for genuinely non-planar input, so these
tests pin both halves: flat polygons become planes, warped ones do not.
"""

from compas.geometry import Box
from compas.geometry import Polygon
from compas.tolerance import TOL
from compas_occt.brep import OCCBrep


def _face_of(polygon):
    brep = OCCBrep.from_polygons([polygon], solid=False)
    assert len(brep.faces) == 1
    return brep.faces[0]


def test_planar_quad_is_a_plane():
    face = _face_of(Polygon([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]))
    assert face.is_plane
    assert TOL.is_close(face.area, 1.0)


def test_planar_quad_off_the_world_planes_is_a_plane():
    """The plane is fitted to the polygon, not guessed from a global axis."""
    face = _face_of(Polygon([[0, 0, 0], [1, 0, 1], [1, 1, 1], [0, 1, 0]]))
    assert face.is_plane


def test_planar_ngon_is_a_plane():
    hexagon = Polygon([[0, 0, 0], [2, 0, 0], [3, 1, 0], [2, 2, 0], [0, 2, 0], [-1, 1, 0]])
    face = _face_of(hexagon)
    assert face.is_plane
    assert TOL.is_close(face.area, 6.0)


def test_planar_triangle_is_a_plane():
    face = _face_of(Polygon([[0, 0, 0], [1, 0, 0], [0, 1, 0]]))
    assert face.is_plane
    assert TOL.is_close(face.area, 0.5)


def test_twisted_quad_is_not_flattened():
    """A genuinely warped quad must keep its ruled surface."""
    face = _face_of(Polygon([[0, 0, 0], [1, 0, 0], [1, 1, 1], [0, 1, 0]]))
    assert not face.is_plane


def test_warped_ngon_is_not_flattened():
    warped = Polygon([[0, 0, 0], [2, 0, 0], [3, 1, 1], [2, 2, 0], [0, 2, 0], [-1, 1, 0]])
    assert not _face_of(warped).is_plane


def test_solid_from_planar_polygons_is_exact_and_planar():
    """The whole point: a box built from its own polygons is a box."""
    box = Box(2)
    brep = OCCBrep.from_polygons(box.polygons, solid=True)

    assert brep.is_solid
    assert len(brep.faces) == 6
    assert all(face.is_plane for face in brep.faces)
    assert TOL.is_close(brep.volume, 8.0)
