"""Reducing a Brep to its wire geometry: `to_curves` and `to_polylines`.

`to_curves` works on any Brep - every edge has an underlying curve, whatever its
type - and it reports each edge once, where exploring `.edges` reports an edge
shared by two faces twice.

`to_polylines` is the flat-polygon case of the same idea. A Brep whose faces are
all planar and bounded by straight edges is fully described by the points of its
loops, so nothing is lost by dropping to polylines. Anything else - a cylinder, a
sphere, a face with an arc in its boundary - would silently lose its curvature,
so the conversion is refused rather than approximated. These tests pin both
halves: what converts, and what is turned away.
"""

import pytest

from compas.geometry import Box
from compas.geometry import Circle
from compas.geometry import Cylinder
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Sphere
from compas.tolerance import TOL
from compas_occt.brep import OCCBrep
from compas_occt.brep import OCCBrepEdge
from compas_occt.brep.errors import BrepError


def _plate_with_a_square_hole():
    return OCCBrep.from_box(Box(10, 10, 1)) - OCCBrep.from_box(Box(2, 2, 5))


def _disk():
    """A planar face whose boundary is a circle, not a chain of straight edges."""
    cylinder = OCCBrep.from_cylinder(Cylinder(radius=1, height=2))
    cap = [face for face in cylinder.faces if face.is_plane][0]
    return OCCBrep.from_brepfaces([cap], solid=False)


def _single_edge():
    """A Brep that is one loose edge, with no faces at all."""
    edge = OCCBrepEdge.from_point_point(Point(0, 0, 0), Point(1, 0, 0))
    return OCCBrep.from_native(edge.occ_edge)


# ==============================================================================
# is_polygonal
# ==============================================================================


def test_box_is_polygonal():
    assert OCCBrep.from_box(Box(1)).is_polygonal


def test_polygons_are_polygonal():
    brep = OCCBrep.from_polygons(Box(2).polygons, solid=True)
    assert brep.is_polygonal


def test_cylinder_is_not_polygonal():
    """Flat caps are not enough - the barrel is curved."""
    brep = OCCBrep.from_cylinder(Cylinder(1, 1))
    assert any(face.is_plane for face in brep.faces)
    assert not brep.is_polygonal


def test_sphere_is_not_polygonal():
    assert not OCCBrep.from_sphere(Sphere(1)).is_polygonal


def test_planar_face_with_curved_boundary_is_not_polygonal():
    """A disk is planar, but its boundary is a circle, not straight edges."""
    disk = _disk()
    assert all(face.is_plane for face in disk.faces)
    assert not disk.is_polygonal


def test_brep_without_faces_is_not_polygonal():
    brep = _single_edge()
    assert brep.faces == []
    assert not brep.is_polygonal


# ==============================================================================
# to_curves
# ==============================================================================


def test_to_curves_reports_every_edge_once():
    """A box has 12 edges, but exploring its faces visits each of them twice."""
    brep = OCCBrep.from_box(Box(1))

    assert len(brep.edges) == 24
    assert len(brep.to_curves()) == 12


def test_to_curves_of_a_box_are_its_lines():
    brep = OCCBrep.from_box(Box(2))
    curves = brep.to_curves()

    assert all(isinstance(curve, Line) for curve in curves)
    assert all(TOL.is_close(curve.length, 2.0) for curve in curves)
    assert TOL.is_close(sum(curve.length for curve in curves), 24.0)


def test_to_curves_keeps_curved_edges_curved():
    """A cylinder reduces to its two rim circles and the seam line."""
    brep = OCCBrep.from_cylinder(Cylinder(radius=1, height=2))
    curves = brep.to_curves()

    circles = [curve for curve in curves if isinstance(curve, Circle)]
    assert len(circles) == 2
    assert all(TOL.is_close(circle.radius, 1.0) for circle in circles)


def test_to_curves_works_without_faces():
    """Curves come off the edges, so a Brep that is one loose edge still converts."""
    curves = _single_edge().to_curves()

    assert len(curves) == 1
    assert isinstance(curves[0], Line)
    assert TOL.is_close(curves[0].length, 1.0)


# ==============================================================================
# to_polylines
# ==============================================================================


def test_to_polylines_of_a_box():
    brep = OCCBrep.from_box(Box(1))
    polylines = brep.to_polylines()

    assert len(polylines) == 6
    assert all(polyline.is_closed for polyline in polylines)
    assert all(len(polyline.points) == 5 for polyline in polylines)
    assert all(TOL.is_close(polyline.length, 4.0) for polyline in polylines)


def test_to_polylines_are_the_face_boundaries():
    """Every polyline traces the outer loop of the face at the same index."""
    brep = OCCBrep.from_box(Box(1, 2, 3))

    for face, polyline in zip(brep.faces, brep.to_polylines()):
        boundary = [vertex.point for vertex in face.outerloop.vertices]
        assert TOL.is_allclose(polyline.points[:-1], boundary)
        assert TOL.is_allclose(polyline.points[0], polyline.points[-1])


def test_to_polylines_includes_the_holes():
    """A plate with a square hole has two faces with an inner loop each."""
    cut = _plate_with_a_square_hole()

    assert cut.is_polygonal
    assert len(cut.faces) == 10

    polylines = cut.to_polylines()
    assert len(polylines) == 12
    assert sum(1 for polyline in polylines if TOL.is_close(polyline.length, 8.0)) == 2


def test_to_polylines_puts_the_outer_loop_first():
    cut = _plate_with_a_square_hole()

    holed = [face for face in cut.faces if len(face.loops) == 2]
    assert len(holed) == 2

    for face in holed:
        outer, inner = OCCBrep.from_brepfaces([face], solid=False).to_polylines()
        assert outer.length > inner.length


def test_to_polylines_of_a_single_polygon():
    polygon = Polygon([[0, 0, 0], [3, 0, 0], [3, 4, 0], [0, 4, 0]])
    brep = OCCBrep.from_polygons([polygon], solid=False)
    polylines = brep.to_polylines()

    assert len(polylines) == 1
    assert TOL.is_close(polylines[0].length, 14.0)


def test_to_polylines_of_a_transformed_box_follows_the_frame():
    box = Box(1, frame=Frame([5, 0, 0], [0, 1, 0], [0, 0, 1]))
    brep = OCCBrep.from_box(box)

    for polyline in brep.to_polylines():
        assert all(TOL.is_close(point.x, 5.0, atol=1.0) for point in polyline.points)


def test_to_polylines_refuses_a_cylinder():
    brep = OCCBrep.from_cylinder(Cylinder(1, 1))
    with pytest.raises(BrepError):
        brep.to_polylines()


def test_to_polylines_refuses_a_sphere():
    with pytest.raises(BrepError):
        OCCBrep.from_sphere(Sphere(1)).to_polylines()


def test_to_polylines_refuses_a_disk():
    """Planar is not enough: a circular boundary has no polygon to fall back on."""
    with pytest.raises(BrepError):
        _disk().to_polylines()


def test_to_polylines_refuses_a_brep_without_faces():
    with pytest.raises(BrepError, match="no faces"):
        _single_edge().to_polylines()


def test_to_polylines_names_the_offending_face():
    with pytest.raises(BrepError, match="Face 0"):
        OCCBrep.from_sphere(Sphere(1)).to_polylines()


# ==============================================================================
# round trip
# ==============================================================================


def test_polylines_rebuild_the_solid():
    """The point of the guard: a polygonal Brep survives the round trip."""
    box = Box(1, 2, 3)
    brep = OCCBrep.from_box(box)

    polygons = [Polygon(polyline.points[:-1]) for polyline in brep.to_polylines()]
    rebuilt = OCCBrep.from_polygons(polygons, solid=True)

    assert rebuilt.is_solid
    assert rebuilt.is_polygonal
    assert TOL.is_close(rebuilt.volume, brep.volume)
    assert TOL.is_close(rebuilt.area, brep.area)
