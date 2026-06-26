import numpy as np

from compas.geometry import Box
from compas.geometry import Point
from compas_occt import _occt
from compas_occt.brep import OCCBrep
from compas_occt.geometry import OCCNurbsCurve


def test_tessellation_is_zero_copy_numpy():
    shape = OCCBrep.from_box(Box(2)).occ_shape
    vertices, triangles, _ = _occt.tesselate(shape, 0.1, 0.5)
    assert isinstance(vertices, np.ndarray) and vertices.dtype == np.float64 and vertices.shape[1] == 3
    assert isinstance(triangles, np.ndarray) and triangles.shape[1] == 3
    # the array views the C++ buffer directly (no copy on the way out)
    assert vertices.flags["OWNDATA"] is False
    assert vertices.flags["C_CONTIGUOUS"] is True


def test_nurbscurve_poles_numpy():
    curve = OCCNurbsCurve.from_points([Point(0, 0, 0), Point(1, 2, 0), Point(3, 0, 1)])
    poles = _occt.nurbscurve_poles(curve.native_curve)
    assert isinstance(poles, np.ndarray) and poles.shape == (3, 3)
    assert poles.flags["OWNDATA"] is False
    # public API still returns COMPAS points
    assert all(isinstance(p, Point) for p in curve.points)
