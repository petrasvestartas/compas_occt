from typing import Optional
from typing import Union

from compas.geometry import Box
from compas.geometry import Curve
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polyline
from compas.geometry import Transformation
from compas.geometry import Vector
from compas.geometry import distance_point_point
from compas.itertools import linspace
from compas_occt import _occt as _curves
from compas_occt.conversions import compas_transformation_to_trsf
from compas_occt.conversions import point_to_compas
from compas_occt.conversions import vector_to_compas

from .curve2d import OCCCurve2d


class OCCCurve(Curve):
    """Class representing a general curve object.

    Parameters
    ----------
    native_curve : GeomCurve
        An existing OCC curve handle wrapper.
    name : str, optional
        The name of the curve.

    Attributes
    ----------
    dimension
        The dimension of the curve.
    domain
        The domain of the parameter space of the curve.
    end
        The end point of the curve.
    is_closed
        Flag indicating that the curve is closed.
    is_periodic
        Flag indicating that the curve is periodic.
    start
        The start point of the curve.

    """

    def __init__(self, native_curve, name=None):
        super().__init__(name=name)
        self._dimension = 3
        self._native_curve = native_curve

    def __eq__(self, other: "OCCCurve") -> bool:
        raise NotImplementedError

    # ==============================================================================
    # OCC Properties
    # ==============================================================================

    @property
    def native_curve(self):
        return self._native_curve

    @native_curve.setter
    def native_curve(self, curve):
        self._native_curve = curve

    @property
    def occ_curve(self):
        return self._native_curve

    @property
    def occ_shape(self):
        return _curves.curve_to_edge(self._native_curve)

    @property
    def occ_edge(self):
        return _curves.curve_to_edge(self._native_curve)

    # ==============================================================================
    # Properties
    # ==============================================================================

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def domain(self) -> tuple[float, float]:
        return _curves.curve_domain(self._native_curve)

    @property
    def start(self) -> Point:
        return self.point_at(self.domain[0])

    @property
    def end(self) -> Point:
        return self.point_at(self.domain[1])

    @property
    def is_closed(self) -> bool:
        return _curves.curve_is_closed(self._native_curve)

    @property
    def is_periodic(self) -> bool:
        return _curves.curve_is_periodic(self._native_curve)

    # ==============================================================================
    # Constructors
    # ==============================================================================

    @classmethod
    def from_native(cls, native_curve) -> "OCCCurve":
        """Construct a curve from an existing OCC curve handle.

        Parameters
        ----------
        native_curve

        Returns
        -------
        OCCCurve

        """
        return cls(native_curve)

    @classmethod
    def from_occ(cls, native_curve) -> "OCCCurve":
        """Construct a curve from an existing OCC curve handle.

        .. deprecated:: 1.3
            Use `from_native` instead.

        """
        return cls(native_curve)

    # ==============================================================================
    # Conversions
    # ==============================================================================

    def to_step(self, filepath: str, schema: str = "AP203") -> None:
        """Write the curve geometry to a STP file."""
        from compas_occt import _occt as _io

        _io.edge_to_step(self.occ_edge, str(filepath), schema)

    def to_points(self, n: int = 10, domain: Optional[tuple[float, float]] = None) -> list[Point]:
        """Convert the curve to a list of ``n`` points (single bulk evaluation)."""
        start, end = domain or self.domain
        params = list(linspace(start, end, n))
        return [Point(*xyz) for xyz in _curves.curve_points_at(self._native_curve, params).tolist()]

    def to_polyline(self, n: int = 100) -> Polyline:
        """Convert the curve to a polyline."""
        return Polyline(self.to_points(n=n))

    # ==============================================================================
    # Methods
    # ==============================================================================

    def copy(self) -> "OCCCurve":
        """Make an independent copy of the current curve."""
        cls = type(self)
        return cls(_curves.curve_copy(self._native_curve))

    def transform(self, T: Transformation) -> None:
        """Transform this curve."""
        _curves.curve_transform(self._native_curve, compas_transformation_to_trsf(T))

    def reverse(self) -> None:
        """Reverse the parametrisation of the curve."""
        _curves.curve_reverse(self._native_curve)

    def point_at(self, t: float) -> Point:
        """Compute the point at a curve parameter.

        Raises
        ------
        ValueError
            If the parameter is not in the curve domain.

        """
        return point_to_compas(_curves.curve_point_at(self._native_curve, t))

    def tangent_at(self, t: float) -> Vector:
        """Compute the tangent vector at a curve parameter.

        Raises
        ------
        ValueError
            If the parameter is not in the curve domain.

        """
        return vector_to_compas(_curves.curve_tangent_at(self._native_curve, t))

    def curvature_at(self, t: float) -> Vector:
        """Compute the curvature vector at a curve parameter.

        Raises
        ------
        ValueError
            If the parameter is not in the curve domain.

        """
        return vector_to_compas(_curves.curve_curvature_at(self._native_curve, t))

    def frame_at(self, t: float) -> Frame:
        """Compute the local frame at a curve parameter.

        Raises
        ------
        ValueError
            If the parameter is not in the curve domain.

        """
        point, uvec, vvec = _curves.curve_frame_at(self._native_curve, t)
        return Frame(point_to_compas(point), vector_to_compas(uvec), vector_to_compas(vvec))

    def parameter_at_distance(self, t: float, distance: float, precision: float = 0.1) -> float:
        """Compute the parameter at a given distance along the curve from a starting parameter."""
        return _curves.curve_parameter_at_distance(self._native_curve, t, distance, precision)

    def aabb(self, precision: float = 0.0) -> Box:
        """Compute the axis aligned bounding box of the curve."""
        cmin, cmax = _curves.curve_aabb(self._native_curve, precision)
        return Box.from_diagonal((point_to_compas(cmin), point_to_compas(cmax)))

    def length(self, precision: float = 1e-3) -> float:
        """Compute the length of the curve."""
        return _curves.curve_length(self._native_curve, precision)

    def closest_point(
        self,
        point: Point,
        return_parameter: bool = False,
    ) -> Union[Point, tuple[Point, float], None]:
        """Compute the closest point on the curve to a given point.

        If an orthogonal projection is not possible, the start or end point is returned,
        whichever is closer.

        """
        result = _curves.curve_closest_point(self._native_curve, list(point))

        if result is not None:
            xyz, parameter = result
            closest = point_to_compas(xyz)
            if not return_parameter:
                return closest
            return closest, parameter

        start = self.start
        end = self.end
        d_start = distance_point_point(point, start)
        d_end = distance_point_point(point, end)
        domain = self.domain
        if d_start <= d_end:
            if not return_parameter:
                return start
            return start, domain[0]
        if not return_parameter:
            return end
        return end, domain[1]

    def closest_parameters_curve(
        self,
        curve: "OCCCurve",
        return_distance: bool = False,
    ) -> Union[tuple[float, float], tuple[tuple[float, float], float]]:
        """Compute the curve parameters where this curve is closest to another curve."""
        u, v, distance = _curves.curve_closest_parameters_curve(self._native_curve, curve._native_curve)
        if not return_distance:
            return u, v
        return (u, v), distance

    def closest_points_curve(
        self,
        curve: "OCCCurve",
        return_distance: bool = False,
    ) -> Union[tuple[Point, Point], tuple[tuple[Point, Point], float]]:
        """Compute the points where this curve is closest to another curve."""
        a, b, distance = _curves.curve_closest_points_curve(self._native_curve, curve._native_curve)
        points = point_to_compas(a), point_to_compas(b)
        if not return_distance:
            return points
        return points, distance

    def divide_by_count(
        self,
        count: int,
        return_points: bool = False,
        precision: float = 1e-6,
    ) -> Union[list[float], tuple[list[float], list[Point]]]:
        """Divide the curve into a specific number of equal length segments."""
        L = self.length(precision=precision)
        length = L / count
        a, b = self.domain
        params = [a]
        params.extend(_curves.curve_abscissa_params(self._native_curve, length, count, precision))
        params.append(b)
        if not return_points:
            return params
        points = [self.point_at(t) for t in params]
        return params, points

    divide = divide_by_count

    def divide_by_length(
        self,
        length: float,
        return_points: bool = False,
        precision: float = 1e-6,
    ) -> Union[list[float], tuple[list[float], list[Point]]]:
        """Divide the curve into segments of a given length.

        Note that the end point of the last segment might not coincide with the end point
        of the curve.

        """
        L = self.length(precision=precision)
        count = int(L / length)
        a, b = self.domain
        params = [a]
        params.extend(_curves.curve_abscissa_params(self._native_curve, length, count, precision))
        params.append(b)
        if not return_points:
            return params
        points = [self.point_at(t) for t in params]
        return params, points

    def projected(self, surface) -> "OCCCurve":
        """Return a copy of the curve projected onto a surface."""
        return OCCCurve.from_native(_curves.curve_projected(self._native_curve, surface.native_surface))

    def embedded(self, surface) -> OCCCurve2d:
        """Return a new curve embedded in the parameter space of the surface."""
        return OCCCurve2d.from_native(_curves.curve_embedded(self._native_curve, surface.native_surface))

    def offset(self, distance: float, direction: Vector) -> "OCCCurve":
        """Return a new curve offset over a distance in the plane defined by the given normal direction."""
        return OCCCurve.from_native(_curves.curve_offset(self._native_curve, distance, list(direction)))
