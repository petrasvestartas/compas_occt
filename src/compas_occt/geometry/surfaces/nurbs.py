import warnings
from copy import deepcopy
from typing import Iterable
from typing import Literal
from typing import Optional
from typing import Union

from compas.geometry import Curve
from compas.geometry import NurbsSurface
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Translation
from compas.geometry import Vector
from compas.itertools import flatten
from compas_occt import _occt as _surfaces
from compas_occt.conversions import point_to_compas
from compas_occt.geometry.curves.nurbs import OCCNurbsCurve

from .surface import OCCSurface


class ControlPoints:
    def __init__(self, surface: "OCCNurbsSurface") -> None:
        self.native_surface = surface.native_surface

    @property
    def points(self) -> list[list[Point]]:
        return [[Point(*xyz) for xyz in row] for row in _surfaces.nurbssurface_poles2(self.native_surface).tolist()]

    def __getitem__(self, index: Union[int, tuple[int, int]]) -> Point:
        try:
            u, v = index  # type: ignore
        except TypeError:
            return self.points[index]  # type: ignore
        else:
            return point_to_compas(_surfaces.nurbssurface_pole(self.native_surface, u + 1, v + 1))

    def __setitem__(self, index: tuple[int, int], point: Point) -> None:
        u, v = index
        _surfaces.nurbssurface_set_pole(self.native_surface, u + 1, v + 1, list(point))

    def __len__(self) -> int:
        return _surfaces.nurbssurface_nb_vpoles(self.native_surface)

    def __iter__(self) -> Iterable:
        return iter(self.points)


class OCCNurbsSurface(OCCSurface, NurbsSurface):
    """Class representing a NURBS surface based on the BSplineSurface of the OCC geometry kernel.

    Parameters
    ----------
    name
        The name of the curve

    Attributes
    ----------
    points
        The control points of the surface.
    weights
        The weights of the control points of the surface.
    knots_u
        The knots of the surface in the U direction, without multiplicities.
    knots_v
        The knots of the surface in the V direction, without multiplicities.
    mults_u
        The multiplicities of the knots of the surface in the U direction.
    mults_v
        The multiplicities of the knots of the surface in the V direction.

    """

    @property
    def __data__(self) -> dict:
        return {
            "points": [[point.__data__ for point in row] for row in self.points],  # type: ignore
            "weights": self.weights,
            "knots_u": self.knots_u,
            "knots_v": self.knots_v,
            "mults_u": self.mults_u,
            "mults_v": self.mults_v,
            "degree_u": self.degree_u,
            "degree_v": self.degree_v,
            "is_periodic_u": self.is_periodic_u,
            "is_periodic_v": self.is_periodic_v,
        }

    @classmethod
    def __from_data__(cls, data: dict) -> "OCCNurbsSurface":
        points = [[Point.__from_data__(point) for point in row] for row in data["points"]]
        weights = data["weights"]
        knots_u = data["knots_u"]
        knots_v = data["knots_v"]
        mults_u = data["mults_u"]
        mults_v = data["mults_v"]
        degree_u = data["degree_u"]
        degree_v = data["degree_v"]
        is_periodic_u = data["is_periodic_u"]
        is_periodic_v = data["is_periodic_v"]
        return OCCNurbsSurface.from_parameters(
            points,
            weights,
            knots_u,
            knots_v,
            mults_u,
            mults_v,
            degree_u,
            degree_v,
            is_periodic_u,
            is_periodic_v,
        )

    def __eq__(self, other: "OCCNurbsSurface") -> bool:
        for a, b in zip(flatten(self.points), flatten(other.points)):
            if a != b:
                return False
        for a, b in zip(flatten(self.weights), flatten(other.weights)):
            if a != b:
                return False
        for a, b in zip(self.knots_u, self.knots_v):
            if a != b:
                return False
        for a, b in zip(self.mults_u, self.mults_v):
            if a != b:
                return False
        if self.degree_u != self.degree_v:
            return False
        if self.is_periodic_u != self.is_periodic_v:
            return False
        return True

    # ==============================================================================
    # Properties
    # ==============================================================================

    @property
    def points(self) -> ControlPoints:
        if not hasattr(self, "_points"):
            self._points = ControlPoints(self)
        return self._points

    @property
    def weights(self) -> list[list[float]]:
        return [list(row) for row in _surfaces.nurbssurface_weights2(self.native_surface)]

    @property
    def degree_u(self) -> int:
        return _surfaces.nurbssurface_degree_u(self.native_surface)

    @property
    def degree_v(self) -> int:
        return _surfaces.nurbssurface_degree_v(self.native_surface)

    @property
    def knots_u(self) -> list[float]:
        return list(_surfaces.nurbssurface_uknots(self.native_surface))

    @property
    def knots_v(self) -> list[float]:
        return list(_surfaces.nurbssurface_vknots(self.native_surface))

    @property
    def mults_u(self) -> list[int]:
        return list(_surfaces.nurbssurface_umults(self.native_surface))

    @property
    def mults_v(self) -> list[int]:
        return list(_surfaces.nurbssurface_vmults(self.native_surface))

    # ==============================================================================
    # Constructors
    # ==============================================================================

    @classmethod
    def from_extrusion(cls, curve: Curve, vector: Vector) -> "OCCNurbsSurface":
        """Construct a NURBS surface from an extrusion of a basis curve.

        Note that the extrusion surface is constructed by generating an infill between
        the basis curve and a translated copy with :meth:`from_fill`.

        """
        other = curve.transformed(Translation.from_vector(vector))
        return cls.from_fill(curve, other)  # type: ignore

    @classmethod
    def from_fill(
        cls,
        curve1: OCCNurbsCurve,
        curve2: OCCNurbsCurve,
        curve3: Optional[OCCNurbsCurve] = None,
        curve4: Optional[OCCNurbsCurve] = None,
        style: Literal["stretch", "coons", "curved"] = "stretch",
    ) -> "OCCNurbsSurface":
        """Construct a NURBS surface from the infill between two, three or four contiguous NURBS curves.

        Parameters
        ----------
        curve1, curve2, curve3, curve4
            The boundary curves.
        style
            The fill style: ``'stretch'`` (flattest), ``'curved'`` (rounded), or ``'coons'`` (between).

        Raises
        ------
        ValueError
            If the fill style is not supported.

        """
        if style not in ("stretch", "coons", "curved"):
            warnings.warn('This fill style is not supported: {}. We will use GeomFill_StretchStyle ("stretch") instead.'.format(style))
            style = "stretch"

        curves = [curve1.occ_curve, curve2.occ_curve]
        if curve3:
            curves.append(curve3.occ_curve)
        if curve4:
            curves.append(curve4.occ_curve)
        native_surface = _surfaces.nurbssurface_from_fill(curves, style)
        return cls.from_native(native_surface)

    @classmethod
    def from_interpolation(cls, points: list[list[Point]], precision: float = 1e-3) -> "OCCNurbsSurface":
        """Construct a NURBS surface by approximating or interpolating a 2D collection of points."""
        grid = [[list(point) for point in row] for row in points]
        native_surface = _surfaces.nurbssurface_from_interpolation(grid, precision)
        return cls(native_surface)

    @classmethod
    def from_native(cls, native_surface) -> "OCCNurbsSurface":
        """Construct a NURBS surface from an existing OCC surface handle."""
        return cls(native_surface)

    @classmethod
    def from_parameters(
        cls,
        points: list[list[Point]],
        weights: list[list[float]],
        knots_u: list[float],
        knots_v: list[float],
        mults_u: list[int],
        mults_v: list[int],
        degree_u: int,
        degree_v: int,
        is_periodic_u: bool = False,
        is_periodic_v: bool = False,
    ) -> "OCCNurbsSurface":
        """Construct a NURBS surface from explicit parameters."""
        grid = [[list(point) for point in row] for row in points]
        wgrid = [[float(w) for w in row] for row in weights]
        native_surface = _surfaces.nurbssurface_from_parameters(
            grid,
            wgrid,
            list(knots_u),
            list(knots_v),
            list(mults_u),
            list(mults_v),
            degree_u,
            degree_v,
            is_periodic_u,
            is_periodic_v,
        )
        return cls.from_native(native_surface)

    @classmethod
    def from_plane(cls, plane: Plane) -> "OCCNurbsSurface":
        """Construct a NURBS surface from a plane."""
        native_surface = _surfaces.nurbssurface_from_plane(list(plane.point), list(plane.normal))
        return cls.from_native(native_surface)

    @classmethod
    def from_points(
        cls,
        points: list[list[Point]],
        degree_u: int = 3,
        degree_v: int = 3,
    ) -> "OCCNurbsSurface":
        """Construct a NURBS surface from control points."""
        u = len(points[0])
        v = len(points)
        weights = [[1.0 for _ in range(u)] for _ in range(v)]
        degree_u = degree_u if u > degree_u else u - 1
        degree_v = degree_v if v > degree_v else v - 1
        u_order = degree_u + 1
        v_order = degree_v + 1
        x = u - u_order
        knots_u = [float(i) for i in range(2 + x)]
        mults_u = [u_order]
        for _ in range(x):
            mults_u.append(1)
        mults_u.append(u_order)
        x = v - v_order
        knots_v = [float(i) for i in range(2 + x)]
        mults_v = [v_order]
        for _ in range(x):
            mults_v.append(1)
        mults_v.append(v_order)
        is_periodic_u = False
        is_periodic_v = False
        return cls.from_parameters(
            points,
            weights,
            knots_u,
            knots_v,
            mults_u,
            mults_v,
            degree_u,
            degree_v,
            is_periodic_u,
            is_periodic_v,
        )

    # ==============================================================================
    # Methods
    # ==============================================================================

    def copy(self) -> "OCCNurbsSurface":
        """Make an independent copy of the current surface."""
        cls = type(self)
        return cls.__from_data__(deepcopy(self.__data__))
