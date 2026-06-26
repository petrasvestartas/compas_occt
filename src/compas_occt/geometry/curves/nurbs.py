from copy import deepcopy
from math import sqrt
from typing import Optional
from typing import Union

from compas.geometry import Arc
from compas.geometry import Circle
from compas.geometry import Ellipse
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import NurbsCurve
from compas.geometry import Point
from compas_occt import _occt as _curves
from compas_occt.conversions import array1_from_floats1
from compas_occt.conversions import array1_from_integers1
from compas_occt.conversions import array1_from_points1
from compas_occt.conversions import point_to_compas

from .curve import OCCCurve


def native_curve_from_parameters(
    points: list[Point],
    weights: list[float],
    knots: list[float],
    multiplicities: list[int],
    degree: int,
    is_periodic: bool,
):
    return _curves.nurbscurve_from_parameters(
        [list(point) for point in points],
        list(weights),
        list(knots),
        list(multiplicities),
        degree,
        is_periodic,
    )


class OCCNurbsCurve(OCCCurve, NurbsCurve):
    """Class representing a NURBS curve based on the BSplineCurve of the OCC geometry kernel.

    Parameters
    ----------
    name
        The name of the curve.

    Attributes
    ----------
    continuity
        The degree of continuity of the curve.
    degree
        The degree of the curve.
    is_rational
        Flag indicating that the curve is rational.
    knots
        The knots of the curve, without multiplicities.
    knotsequence
        The full vector of knots of the curve.
    multiplicities
        The multiplicities of the knots of the curve.
    order
        The order of the curve (= degree + 1).
    points
        The control points of the curve.
    weights
        The weights of the control points of the curve.

    Examples
    --------
    >>> from compas.geometry import Point
    >>> from compas_occt.geometry import OCCNurbsCurve
    >>> points = [Point(0, 0, 0), Point(3, 6, 0), Point(6, -3, 3), Point(10, 0, 0)]
    >>> curve = OCCNurbsCurve.from_points(points)

    """

    @property
    def __data__(self) -> dict:
        return {
            "points": [point.__data__ for point in self.points],
            "weights": self.weights,
            "knots": self.knots,
            "multiplicities": self.multiplicities,
            "degree": self.degree,
            "is_periodic": self.is_periodic,
        }

    @classmethod
    def __from_data__(cls, data: dict) -> "OCCNurbsCurve":
        points = [Point.__from_data__(point) for point in data["points"]]
        weights = data["weights"]
        knots = data["knots"]
        multiplicities = data["multiplicities"]
        degree = data["degree"]
        is_periodic = data["is_periodic"]
        return cls.from_parameters(
            points,
            weights,
            knots,
            multiplicities,
            degree,
            is_periodic,
        )

    def __init__(self, native_curve, name: Optional[str] = None):
        super(OCCNurbsCurve, self).__init__(native_curve, name=name)

    # ==============================================================================
    # OCC Properties
    # ==============================================================================

    @property
    def occ_curve(self):
        return self.native_curve

    @property
    def occ_points(self):
        return array1_from_points1(self.points)

    @property
    def occ_weights(self):
        return array1_from_floats1(self.weights)

    @property
    def occ_knots(self):
        return array1_from_floats1(self.knots)

    @property
    def occ_knotsequence(self):
        return array1_from_floats1(self.knotsequence)

    @property
    def occ_multiplicities(self):
        return array1_from_integers1(self.multiplicities)

    # ==============================================================================
    # Properties
    # ==============================================================================

    @property
    def start(self) -> Point:
        return point_to_compas(_curves.nurbscurve_start(self.native_curve))

    @property
    def end(self) -> Point:
        return point_to_compas(_curves.nurbscurve_end(self.native_curve))

    @property
    def points(self) -> list[Point]:
        return [Point(*xyz) for xyz in _curves.nurbscurve_poles(self.native_curve).tolist()]

    @property
    def weights(self) -> list[float]:
        return list(_curves.nurbscurve_weights(self.native_curve))

    @property
    def knots(self) -> list[float]:
        return list(_curves.nurbscurve_knots(self.native_curve))

    @property
    def knotsequence(self) -> list[float]:
        return list(_curves.nurbscurve_knotsequence(self.native_curve))

    @property
    def multiplicities(self) -> list[int]:
        return list(_curves.nurbscurve_multiplicities(self.native_curve))

    @property
    def continuity(self) -> int:
        return _curves.nurbscurve_continuity(self.native_curve)

    @property
    def degree(self) -> int:
        return _curves.nurbscurve_degree(self.native_curve)

    @property
    def order(self) -> int:
        return self.degree + 1

    @property
    def is_rational(self) -> bool:
        return _curves.nurbscurve_is_rational(self.native_curve)

    # ==============================================================================
    # Constructors
    # ==============================================================================

    @classmethod
    def from_arc(cls, arc: Arc, degree: int, pointcount: Optional[int] = None) -> "OCCNurbsCurve":
        """Construct a NURBS curve from an arc."""
        raise NotImplementedError

    @classmethod
    def from_circle(cls, circle: Circle) -> "OCCNurbsCurve":
        """Construct a NURBS curve from a circle."""
        frame = Frame.from_plane(circle.plane)
        w = 0.5 * sqrt(2)
        dx = frame.xaxis * circle.radius
        dy = frame.yaxis * circle.radius
        points = [
            frame.point - dy,
            frame.point - dy - dx,
            frame.point - dx,
            frame.point + dy - dx,
            frame.point + dy,
            frame.point + dy + dx,
            frame.point + dx,
            frame.point - dy + dx,
            frame.point - dy,
        ]
        knots = [0, 1 / 4, 1 / 2, 3 / 4, 1]
        mults = [3, 2, 2, 2, 3]
        weights = [1, w, 1, w, 1, w, 1, w, 1]
        return cls.from_parameters(
            points=points,
            weights=weights,
            knots=knots,
            multiplicities=mults,
            degree=2,
        )

    @classmethod
    def from_ellipse(cls, ellipse: Ellipse) -> "OCCNurbsCurve":
        """Construct a NURBS curve from an ellipse."""
        frame = Frame.from_plane(ellipse.plane)
        frame = Frame.worldXY()
        w = 0.5 * sqrt(2)
        dx = frame.xaxis * ellipse.major
        dy = frame.yaxis * ellipse.minor
        points = [
            frame.point - dy,
            frame.point - dy - dx,
            frame.point - dx,
            frame.point + dy - dx,
            frame.point + dy,
            frame.point + dy + dx,
            frame.point + dx,
            frame.point - dy + dx,
            frame.point - dy,
        ]
        knots = [0, 1 / 4, 1 / 2, 3 / 4, 1]
        mults = [3, 2, 2, 2, 3]
        weights = [1, w, 1, w, 1, w, 1, w, 1]
        return cls.from_parameters(
            points=points,
            weights=weights,
            knots=knots,
            multiplicities=mults,
            degree=2,
        )

    @classmethod
    def from_interpolation(cls, points: list[Point], precision: float = 1e-3) -> "OCCNurbsCurve":
        """Construct a NURBS curve by interpolating a set of points."""
        native_curve = _curves.nurbscurve_from_interpolation([list(point) for point in points], precision)
        return cls.from_native(native_curve)

    @classmethod
    def from_line(cls, line: Line) -> "OCCNurbsCurve":
        """Construct a NURBS curve from a line."""
        return cls.from_parameters(
            points=[line.start, line.end],
            weights=[1.0, 1.0],
            knots=[0.0, 1.0],
            multiplicities=[2, 2],
            degree=1,
        )

    @classmethod
    def from_native(cls, native_curve) -> "OCCNurbsCurve":
        """Construct a NURBS curve from an existing OCC BSplineCurve handle."""
        return cls(native_curve)

    @classmethod
    def from_parameters(
        cls,
        points: list[Point],
        weights: list[float],
        knots: list[float],
        multiplicities: list[int],
        degree: int,
        is_periodic: bool = False,
    ) -> "OCCNurbsCurve":
        """Construct a NURBS curve from explicit curve parameters."""
        native_curve = native_curve_from_parameters(
            points,
            weights,
            knots,
            multiplicities,
            degree,
            is_periodic,
        )
        return cls.from_native(native_curve)

    @classmethod
    def from_points(cls, points: list[Point], degree: int = 3) -> "OCCNurbsCurve":
        """Construct a NURBS curve from control points."""
        p = len(points)
        weights = [1.0] * p
        degree = degree if p > degree else p - 1
        order = degree + 1
        x = p - order
        knots = [float(i) for i in range(2 + x)]
        multiplicities = [order]
        for _ in range(x):
            multiplicities.append(1)
        multiplicities.append(order)
        is_periodic = False
        native_curve = native_curve_from_parameters(
            points,
            weights,
            knots,
            multiplicities,
            degree,
            is_periodic,
        )
        return cls.from_native(native_curve)

    # ==============================================================================
    # Methods
    # ==============================================================================

    def copy(self) -> "OCCNurbsCurve":
        """Make an independent copy of the current curve."""
        cls = type(self)
        return cls.__from_data__(deepcopy(self.__data__))

    def segment(self, u: float, v: float, precision: float = 1e-3) -> None:
        """Modify this curve by segmenting it between the parameters u and v."""
        if u > v:
            u, v = v, u
        s, e = self.domain
        if u < s or v > e:
            raise ValueError("At least one of the given parameters is outside the curve domain.")
        if u == v:
            raise ValueError("The given domain is zero length.")
        _curves.nurbscurve_segment(self.native_curve, u, v, precision)

    def segmented(self, u: float, v: float, precision: float = 1e-3) -> "OCCNurbsCurve":
        """Return a copy of this curve segmented between the parameters u and v."""
        copy = self.copy()
        copy.segment(u, v, precision)
        return copy

    def join(self, curve: "OCCNurbsCurve", precision: float = 1e-4) -> None:
        """Modify this curve by joining it with another curve."""
        result, success = _curves.nurbscurve_join(self.native_curve, curve.native_curve, precision)
        if success:
            self.native_curve = result

    def joined(self, curve: "OCCNurbsCurve", precision: float = 1e-4) -> Union["OCCNurbsCurve", None]:
        """Return a new curve that is the result of joining this curve with another."""
        copy = self.copy()
        result, success = _curves.nurbscurve_join(self.native_curve, curve.native_curve, precision)
        if success:
            copy.native_curve = result
            return copy
