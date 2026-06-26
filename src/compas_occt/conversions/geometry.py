"""Geometry conversions between COMPAS and the OCC backend.

``compas_occt`` uses a *functional* C++ backend: OCC ``gp_*`` primitives never cross into
Python. Where ``compas_occ`` passed/returned ``gp_Pnt``/``gp_Ax3``/``gp_Circ`` etc., these
helpers instead use a small, explicit **plain-data** vocabulary:

================  ==========================================================
concept           plain-data representation
================  ==========================================================
point / vector    ``(x, y, z)``
axis / line       ``(location3, direction3)``
frame (ax2/ax3)   ``(point3, xaxis3, yaxis3)``
plane (pln)       ``(point3, normal3)``
circle            ``(frame, radius)``
ellipse           ``(frame, major, minor)``
hyperbola         ``(frame, major, minor)``
parabola          ``(frame, focal)``
sphere            ``(frame, radius)``
cylinder          ``(frame, radius[, height])``
cone              ``(frame, radius, height)``
torus             ``(frame, radius_axis, radius_pipe)``
location          ``3x4`` row-major matrix
aabb              ``(cornermin3, cornermax3)``
obb               ``(frame, xhsize, yhsize, zhsize)``
================  ==========================================================

The ``*_to_occ`` builders return these tuples (the C++ free functions accept them directly).
The ``*_to_compas`` builders accept the same tuples (as produced by the C++ adaptor/explorer
functions) and return COMPAS objects, matching ``compas_occ``'s function names and roles.
"""

from typing import Optional
from typing import Type

from compas.geometry import Bezier
from compas.geometry import Box
from compas.geometry import Circle
from compas.geometry import Cone
from compas.geometry import Cylinder
from compas.geometry import Ellipse
from compas.geometry import Frame
from compas.geometry import Hyperbola
from compas.geometry import Line
from compas.geometry import NurbsCurve
from compas.geometry import Parabola
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Sphere
from compas.geometry import Torus
from compas.geometry import Transformation
from compas.geometry import Vector

Triple = tuple
FrameData = tuple

# =============================================================================
# To OCC (plain data)
# =============================================================================


def point_to_occ(point: Point) -> tuple:
    """Convert a COMPAS point to OCC point data ``(x, y, z)``."""
    return (point[0], point[1], point[2])


def point_to_occ2d(point: Point) -> tuple:
    """Convert a COMPAS point to OCC 2D point data ``(x, y)``."""
    return (point[0], point[1])


def vector_to_occ(vector: Vector) -> tuple:
    """Convert a COMPAS vector to OCC vector data ``(x, y, z)``."""
    return (vector[0], vector[1], vector[2])


def vector_to_occ2d(vector: Vector) -> tuple:
    """Convert a COMPAS vector to OCC 2D vector data ``(x, y)``."""
    return (vector[0], vector[1])


def direction_to_occ(vector: Vector) -> tuple:
    """Convert a COMPAS vector to OCC direction data ``(x, y, z)``."""
    return (vector[0], vector[1], vector[2])


def direction_to_occ2d(vector: Vector) -> tuple:
    """Convert a COMPAS vector to OCC 2D direction data ``(x, y)``."""
    return (vector[0], vector[1])


def axis_to_occ(axis: tuple[Point, Vector]) -> tuple:
    """Convert a COMPAS (point, vector) to OCC axis data ``(location, direction)``."""
    return (point_to_occ(axis[0]), direction_to_occ(axis[1]))


def line_to_occ(line: Line) -> tuple:
    """Convert a COMPAS line to OCC line data ``(location, direction)``."""
    return (point_to_occ(line.start), direction_to_occ(line.direction))


def line_to_occ2d(line: Line) -> tuple:
    """Convert a COMPAS line to OCC 2D line data ``(location, direction)``."""
    return (point_to_occ2d(line.start), direction_to_occ2d(line.direction))


def plane_to_occ(plane: Plane) -> tuple:
    """Convert a COMPAS plane to OCC plane data ``(point, normal)``."""
    return (point_to_occ(plane.point), direction_to_occ(plane.normal))


def plane_to_occ_ax2(plane: Plane) -> tuple:
    """Convert a COMPAS plane to OCC ax2 data ``(point, normal)``."""
    return (point_to_occ(plane.point), direction_to_occ(plane.normal))


def plane_to_occ_ax3(plane: Plane) -> tuple:
    """Convert a COMPAS plane to OCC ax3 data ``(point, normal)``."""
    return (point_to_occ(plane.point), direction_to_occ(plane.normal))


def frame_to_occ_ax2(frame: Frame) -> tuple:
    """Convert a COMPAS frame to OCC ax2 data ``(point, xaxis, yaxis)``."""
    return (point_to_occ(frame.point), direction_to_occ(frame.xaxis), direction_to_occ(frame.yaxis))


def frame_to_occ_ax22d(frame: Frame) -> tuple:
    """Convert a COMPAS frame to OCC ax22d data ``(point, xaxis, yaxis)`` (2D)."""
    return (point_to_occ2d(frame.point), direction_to_occ2d(frame.xaxis), direction_to_occ2d(frame.yaxis))


def frame_to_occ_ax3(frame: Frame) -> tuple:
    """Convert a COMPAS frame to OCC ax3 data ``(point, xaxis, yaxis)``."""
    return (point_to_occ(frame.point), direction_to_occ(frame.xaxis), direction_to_occ(frame.yaxis))


def circle_to_occ(circle: Circle) -> tuple:
    """Convert a COMPAS circle to OCC circle data ``(frame, radius)``."""
    return (frame_to_occ_ax2(circle.frame), circle.radius)


def circle_to_occ2d(circle: Circle) -> tuple:
    """Convert a COMPAS circle to OCC 2D circle data ``(frame, radius)``."""
    return (frame_to_occ_ax22d(circle.frame), circle.radius)


def ellipse_to_occ(ellipse: Ellipse) -> tuple:
    """Convert a COMPAS ellipse to OCC ellipse data ``(frame, major, minor)``."""
    return (frame_to_occ_ax2(ellipse.frame), ellipse.major, ellipse.minor)


def ellipse_to_occ2d(ellipse: Ellipse) -> tuple:
    """Convert a COMPAS ellipse to OCC 2D ellipse data ``(frame, major, minor)``."""
    return (frame_to_occ_ax22d(ellipse.frame), ellipse.major, ellipse.minor)


def sphere_to_occ(sphere: Sphere) -> tuple:
    """Convert a COMPAS sphere to OCC sphere data ``(frame, radius)``."""
    return (frame_to_occ_ax3(sphere.frame), sphere.radius)


def cylinder_to_occ(cylinder: Cylinder) -> tuple:
    """Convert a COMPAS cylinder to OCC cylinder data ``(frame, radius)``."""
    return (frame_to_occ_ax3(cylinder.frame), cylinder.radius)


def cone_to_occ(cone: Cone) -> tuple:
    """Convert a COMPAS cone to OCC cone data ``(frame, radius, height)``."""
    return (frame_to_occ_ax3(cone.frame), cone.radius, cone.height)


def torus_to_occ(torus: Torus) -> tuple:
    """Convert a COMPAS torus to OCC torus data ``(frame, radius_axis, radius_pipe)``."""
    return (frame_to_occ_ax3(torus.frame), torus.radius_axis, torus.radius_pipe)


# =============================================================================
# To COMPAS
# =============================================================================


def point_to_compas(point, cls: Optional[Type[Point]] = None) -> Point:
    """Construct a COMPAS point from OCC point data ``(x, y, z)``."""
    cls = cls or Point
    return cls(point[0], point[1], point[2])


def point2d_to_compas(point, cls: Optional[Type[Point]] = None) -> Point:
    """Construct a COMPAS point from OCC 2D point data ``(x, y)``."""
    cls = cls or Point
    return cls(point[0], point[1], 0)


def vector_to_compas(vector, cls: Optional[Type[Vector]] = None) -> Vector:
    """Construct a COMPAS vector from OCC vector data ``(x, y, z)``."""
    cls = cls or Vector
    return cls(vector[0], vector[1], vector[2])


def vector2d_to_compas(vector, cls: Optional[Type[Vector]] = None) -> Vector:
    """Construct a COMPAS vector from OCC 2D vector data ``(x, y)``."""
    cls = cls or Vector
    return cls(vector[0], vector[1], 0)


def direction_to_compas(vector, cls: Optional[Type[Vector]] = None) -> Vector:
    """Construct a COMPAS vector from OCC direction data ``(x, y, z)``."""
    cls = cls or Vector
    return cls(vector[0], vector[1], vector[2])


def direction2d_to_compas(direction, cls: Optional[Type[Vector]] = None) -> Vector:
    """Construct a COMPAS vector from OCC 2D direction data ``(x, y)``."""
    cls = cls or Vector
    return cls(direction[0], direction[1], 0)


def axis_to_compas_vector(axis, cls: Optional[Type[Vector]] = None) -> Vector:
    """Construct a COMPAS vector from OCC axis data ``(location, direction)``."""
    return direction_to_compas(axis[1], cls=cls)


def axis2d_to_compas_vector(axis, cls: Optional[Type[Vector]] = None) -> Vector:
    """Construct a COMPAS vector from OCC 2D axis data ``(location, direction)``."""
    return direction2d_to_compas(axis[1], cls=cls)


def axis_to_compas(axis) -> tuple[Point, Vector]:
    """Convert OCC axis data ``(location, direction)`` to a ``(Point, Vector)`` tuple."""
    return point_to_compas(axis[0]), direction_to_compas(axis[1])


def axis2d_to_compas(axis) -> tuple[Point, Vector]:
    """Convert OCC 2D axis data ``(location, direction)`` to a ``(Point, Vector)`` tuple."""
    return point2d_to_compas(axis[0]), direction2d_to_compas(axis[1])


def line_to_compas(lin, cls: Optional[Type[Line]] = None) -> Line:
    """Convert OCC line data ``(location, direction)`` to a COMPAS line."""
    cls = cls or Line
    point = point_to_compas(lin[0])
    vector = direction_to_compas(lin[1])
    return cls(point, point + vector)


def line2d_to_compas(lin, cls: Optional[Type[Line]] = None) -> Line:
    """Convert OCC 2D line data ``(location, direction)`` to a COMPAS line."""
    cls = cls or Line
    point = point2d_to_compas(lin[0])
    vector = direction2d_to_compas(lin[1])
    return cls(point, point + vector)


def plane_to_compas(pln, cls: Optional[Type[Plane]] = None) -> Plane:
    """Convert OCC plane data ``(point, normal)`` to a COMPAS plane."""
    cls = cls or Plane
    return cls(point_to_compas(pln[0]), direction_to_compas(pln[1]))


def ax2_to_compas(position, cls: Optional[Type[Frame]] = None) -> Frame:
    """Construct a COMPAS frame from OCC ax2 data ``(point, xaxis, yaxis)``."""
    cls = cls or Frame
    return cls(point_to_compas(position[0]), direction_to_compas(position[1]), direction_to_compas(position[2]))


def ax22d_to_compas(position, cls: Optional[Type[Frame]] = None) -> Frame:
    """Construct a COMPAS frame from OCC ax22d data ``(point, xaxis, yaxis)``."""
    cls = cls or Frame
    return cls(point2d_to_compas(position[0]), direction2d_to_compas(position[1]), direction2d_to_compas(position[2]))


def ax3_to_compas(position, cls: Optional[Type[Frame]] = None) -> Frame:
    """Construct a COMPAS frame from OCC ax3 data ``(point, xaxis, yaxis)``."""
    cls = cls or Frame
    return cls(point_to_compas(position[0]), direction_to_compas(position[1]), direction_to_compas(position[2]))


def location_to_compas(matrix) -> Frame:
    """Construct a COMPAS frame from an OCC location's 3x4 row-major matrix."""
    rows = [list(row) for row in matrix]
    rows.append([0.0, 0.0, 0.0, 1.0])  # COMPAS wants a 4x4 matrix
    return Frame.from_transformation(Transformation(rows))


def circle_to_compas(circ, cls: Optional[Type[Circle]] = None) -> Circle:
    """Construct a COMPAS circle from OCC circle data ``(frame, radius)``."""
    cls = cls or Circle
    frame = ax2_to_compas(circ[0])
    return cls(circ[1], frame=frame)


def circle2d_to_compas(circ, cls: Optional[Type[Circle]] = None) -> Circle:
    """Construct a COMPAS circle from OCC 2D circle data ``(frame, radius)``."""
    cls = cls or Circle
    frame = ax22d_to_compas(circ[0])
    return cls(circ[1], frame=frame)


def ellipse_to_compas(elips, cls: Optional[Type[Ellipse]] = None) -> Ellipse:
    """Construct a COMPAS ellipse from OCC ellipse data ``(frame, major, minor)``."""
    cls = cls or Ellipse
    frame = ax2_to_compas(elips[0])
    return cls(elips[1], elips[2], frame=frame)


def ellipse2d_to_compas(elips, cls: Optional[Type[Ellipse]] = None) -> Ellipse:
    """Construct a COMPAS ellipse from OCC 2D ellipse data ``(frame, major, minor)``."""
    cls = cls or Ellipse
    frame = ax22d_to_compas(elips[0])
    return cls(elips[1], elips[2], frame=frame)


def hyperbola_to_compas(hypr) -> Hyperbola:
    """Construct a COMPAS hyperbola from OCC hyperbola data ``(frame, major, minor)``."""
    frame = ax2_to_compas(hypr[0])
    return Hyperbola(hypr[1], hypr[2], frame=frame)


def hyperbola2d_to_compas(hypr) -> Hyperbola:
    """Construct a COMPAS hyperbola from OCC 2D hyperbola data ``(frame, major, minor)``."""
    frame = ax22d_to_compas(hypr[0])
    return Hyperbola(hypr[1], hypr[2], frame=frame)


def parabola_to_compas(parab) -> Parabola:
    """Construct a COMPAS parabola from OCC parabola data ``(frame, focal)``."""
    frame = ax2_to_compas(parab[0])
    return Parabola(parab[1], frame=frame)


def parabola2d_to_compas(parab) -> Parabola:
    """Construct a COMPAS parabola from OCC 2D parabola data ``(frame, focal)``."""
    frame = ax22d_to_compas(parab[0])
    return Parabola(parab[1], frame=frame)


def bezier_to_compas(points) -> Bezier:
    """Construct a COMPAS Bezier curve from a list of control points."""
    return Bezier([point_to_compas(p) for p in points])


def bspline_to_compas(bspline) -> NurbsCurve:
    """Construct a COMPAS NURBS curve from an OCC B-spline curve handle (``GeomCurve``)."""
    return NurbsCurve.from_native(bspline)


def cylinder_to_compas(cylinder, cls: Optional[Type[Cylinder]] = None) -> Cylinder:
    """Convert OCC cylinder data ``(frame, radius)`` to a COMPAS cylinder."""
    cls = cls or Cylinder
    frame = ax3_to_compas(cylinder[0])
    height = cylinder[2] if len(cylinder) > 2 else 1.0
    return cls(cylinder[1], height, frame=frame)


def sphere_to_compas(sphere, cls: Optional[Type[Sphere]] = None) -> Sphere:
    """Convert OCC sphere data ``(frame, radius)`` to a COMPAS sphere."""
    cls = cls or Sphere
    frame = ax3_to_compas(sphere[0])
    return cls(sphere[1], frame=frame)


def obb_to_compas(obb) -> Box:
    """Convert OCC OBB data ``(frame, xhsize, yhsize, zhsize)`` to a COMPAS box."""
    frame = ax3_to_compas(obb[0])
    return Box(2 * obb[1], 2 * obb[2], 2 * obb[3], frame=frame)


def aabb_to_compas(aabb) -> Box:
    """Convert OCC AABB data ``(cornermin, cornermax)`` to a COMPAS box."""
    return Box.from_diagonal([point_to_compas(aabb[0]), point_to_compas(aabb[1])])
