from compas.geometry import Curve
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polyline
from compas.geometry import Vector
from compas_occt import _occt as _curves
from compas_occt.conversions import point2d_to_compas
from compas_occt.conversions import vector2d_to_compas


class OCCCurve2d(Curve):
    """Class representing a general 2D curve, usually generated through an embedding in a surface.

    Parameters
    ----------
    native_curve : Geom2dCurve
        An existing OCC 2D curve handle wrapper.
    name : str, optional
        The name of the curve.

    Attributes
    ----------
    dimension
        The dimension of the curve is always 2.
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
        self._dimension = 2
        self._native_curve = native_curve

    def __eq__(self, other: "OCCCurve2d") -> bool:
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
        return _curves.curve2d_to_edge(self._native_curve)

    @property
    def occ_edge(self):
        return _curves.curve2d_to_edge(self._native_curve)

    # ==============================================================================
    # Properties
    # ==============================================================================

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def domain(self) -> tuple[float, float]:
        return _curves.curve2d_domain(self._native_curve)

    @property
    def start(self) -> Point:
        return self.point_at(self.domain[0])

    @property
    def end(self) -> Point:
        return self.point_at(self.domain[1])

    @property
    def is_closed(self) -> bool:
        return _curves.curve2d_is_closed(self._native_curve)

    @property
    def is_periodic(self) -> bool:
        return _curves.curve2d_is_periodic(self._native_curve)

    # ==============================================================================
    # Constructors
    # ==============================================================================

    @classmethod
    def from_native(cls, native_curve) -> "OCCCurve2d":
        """Construct a 2D curve from an existing OCC Geom2d curve handle."""
        return cls(native_curve)

    @classmethod
    def from_occ(cls, native_curve) -> "OCCCurve2d":
        """Construct a 2D curve from an existing OCC Geom2d curve handle.

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

    def to_polyline(self, n: int = 100) -> Polyline:
        """Convert the curve to a polyline."""
        return Polyline(self.to_points(n=n))

    # ==============================================================================
    # Methods
    # ==============================================================================

    def copy(self) -> "OCCCurve2d":
        """Make an independent copy of the current curve."""
        cls = type(self)
        return cls(_curves.curve2d_copy(self._native_curve))

    def point_at(self, t: float) -> Point:
        """Compute the point at a curve parameter.

        Raises
        ------
        ValueError
            If the parameter is not in the curve domain.

        """
        return point2d_to_compas(_curves.curve2d_point_at(self._native_curve, t))

    def tangent_at(self, t: float) -> Vector:
        """Compute the tangent vector at a curve parameter.

        Raises
        ------
        ValueError
            If the parameter is not in the curve domain.

        """
        return vector2d_to_compas(_curves.curve2d_tangent_at(self._native_curve, t))

    def curvature_at(self, t: float) -> Vector:
        """Compute the curvature vector at a curve parameter.

        Raises
        ------
        ValueError
            If the parameter is not in the curve domain.

        """
        return vector2d_to_compas(_curves.curve2d_curvature_at(self._native_curve, t))

    def frame_at(self, t: float) -> Frame:
        """Compute the local frame at a curve parameter.

        Raises
        ------
        ValueError
            If the parameter is not in the curve domain.

        """
        point, uvec, vvec = _curves.curve2d_frame_at(self._native_curve, t)
        return Frame(point2d_to_compas(point), vector2d_to_compas(uvec), vector2d_to_compas(vvec))
