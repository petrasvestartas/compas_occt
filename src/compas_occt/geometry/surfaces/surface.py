from typing import Optional
from typing import Union

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Surface
from compas.geometry import Transformation
from compas.geometry import Vector
from compas_occt import _occt as _surfaces
from compas_occt.conversions import ax3_to_compas
from compas_occt.conversions import direction_to_compas
from compas_occt.conversions import point_to_compas
from compas_occt.conversions import vector_to_compas
from compas_occt.geometry.curves.curve import OCCCurve


class OCCSurface(Surface):
    """Class representing a general surface object.

    Parameters
    ----------
    native_surface
        The native OCC surface handle wrapper.
    name
        The name of the surface.

    Attributes
    ----------
    continuity
        The degree of continuity of the surface.
    degree_u
        The degree of the surface in the U direction.
    degree_v
        The degree of the surface in the V direction.
    domain_u
        The parameter domain of the surface in the U direction.
    domain_v
        The parameter domain of the surface in the V direction.
    is_periodic_u
        Flag indicating if the surface is periodic in the U direction.
    is_periodic_v
        Flag indicating if the surface is periodic in the V direction.

    """

    def __init__(self, native_surface, name: Optional[str] = None):
        super().__init__(name=name)
        self.native_surface = native_surface

    @property
    def native_surface(self):
        return self._native_surface

    @native_surface.setter
    def native_surface(self, surface) -> None:
        self._native_surface = surface

    @property
    def occ_surface(self):
        return self._native_surface

    # ==============================================================================
    # OCC Properties
    # ==============================================================================

    @property
    def occ_shape(self):
        return _surfaces.surface_to_face(self._native_surface)

    @property
    def occ_face(self):
        return _surfaces.surface_to_face(self._native_surface)

    # ==============================================================================
    # Properties
    # ==============================================================================

    @property
    def domain_u(self) -> tuple[float, float]:
        umin, umax, _, _ = _surfaces.surface_bounds(self._native_surface)
        return umin, umax

    @property
    def domain_v(self) -> tuple[float, float]:
        _, _, vmin, vmax = _surfaces.surface_bounds(self._native_surface)
        return vmin, vmax

    @property
    def is_periodic_u(self) -> bool:
        return _surfaces.surface_is_periodic_u(self._native_surface)

    @property
    def is_periodic_v(self) -> bool:
        return _surfaces.surface_is_periodic_v(self._native_surface)

    # ==============================================================================
    # Constructors
    # ==============================================================================

    @classmethod
    def from_face(cls, face) -> "OCCSurface":
        """Construct a surface from an existing OCC TopoDS_Face (``Shape``)."""
        return cls.from_native(_surfaces.surface_from_face(face))

    @classmethod
    def from_native(cls, native_surface) -> "OCCSurface":
        """Construct a surface from an existing OCC surface handle."""
        return cls(native_surface)

    @classmethod
    def from_occ(cls, native_surface) -> "OCCSurface":
        """Construct a surface from an existing OCC surface handle.

        .. deprecated:: 1.3
            Use `from_native` instead

        """
        return cls(native_surface)

    # ==============================================================================
    # Conversions
    # ==============================================================================

    def to_step(self, filepath: str, schema: str = "AP203") -> None:
        """Write the surface geometry to a STP file."""
        from compas_occt import _occt as _io

        _io.face_to_step(self.occ_face, str(filepath), schema)

    def to_tesselation(self) -> Mesh:
        """Convert the surface to a triangle mesh."""
        from compas_occt import _occt as _meshing

        vertices, triangles, _ = _meshing.tesselate(self.occ_shape, 0.1, 0.5)
        return Mesh.from_vertices_and_faces(vertices, triangles)

    # ==============================================================================
    # Methods
    # ==============================================================================

    def copy(self) -> "OCCSurface":
        """Make an independent copy of the current surface."""
        cls = type(self)
        return cls.from_native(_surfaces.surface_copy(self._native_surface))

    def transform(self, T: Transformation) -> None:
        """Transform this surface."""
        _surfaces.surface_transform(self._native_surface, list(T.list[:12]))

    def isocurve_u(self, u: float) -> OCCCurve:
        """Compute the isoparametric curve at parameter u."""
        return OCCCurve.from_native(_surfaces.surface_uiso(self._native_surface, u))

    def isocurve_v(self, v: float) -> OCCCurve:
        """Compute the isoparametric curve at parameter v."""
        return OCCCurve.from_native(_surfaces.surface_viso(self._native_surface, v))

    def boundary(self) -> list[OCCCurve]:
        """Compute the boundary curves of the surface."""
        umin, umax, vmin, vmax = _surfaces.surface_bounds(self._native_surface)
        curves = [
            self.isocurve_v(vmin),
            self.isocurve_u(umax),
            self.isocurve_v(vmax),
            self.isocurve_u(umin),
        ]
        curves[-2].reverse()
        curves[-1].reverse()
        return curves

    def point_at(self, u: float, v: float) -> Point:
        """Compute a point on the surface."""
        return point_to_compas(_surfaces.surface_point_at(self._native_surface, u, v))

    def curvature_at(self, u: float, v: float) -> Vector:
        """Compute the curvature at a point on the surface."""
        return direction_to_compas(_surfaces.surface_normal_at(self._native_surface, u, v))

    def gaussian_curvature_at(self, u: float, v: float) -> float:
        """Compute the Gaussian curvature at a point on the surface."""
        return _surfaces.surface_gaussian_curvature_at(self._native_surface, u, v)

    def mean_curvature_at(self, u: float, v: float) -> float:
        """Compute the mean curvature at a point on the surface."""
        return _surfaces.surface_mean_curvature_at(self._native_surface, u, v)

    def frame_at(self, u: float, v: float) -> Frame:
        """Compute the local frame at a point on the surface."""
        point, uvec, vvec = _surfaces.surface_frame_at(self._native_surface, u, v)
        return Frame(point_to_compas(point), vector_to_compas(uvec), vector_to_compas(vvec))

    def aabb(self, precision: float = 0.0, optimal: bool = False) -> Box:
        """Compute the axis aligned bounding box of the surface."""
        cmin, cmax = _surfaces.surface_aabb(self._native_surface, precision, optimal)
        return Box.from_diagonal((point_to_compas(cmin), point_to_compas(cmax)))

    def closest_point(
        self,
        point: Point,
        return_parameters: bool = False,
    ) -> Union[Point, tuple[Point, tuple[float, float]]]:
        """Compute the closest point on the surface to a given point."""
        nearest, u, v = _surfaces.surface_closest_point(self._native_surface, list(point))
        closest = point_to_compas(nearest)
        if not return_parameters:
            return closest
        return closest, (u, v)

    def obb(self, precision: float = 0.0) -> Box:
        """Compute the oriented bounding box of the surface."""
        frame, xh, yh, zh = _surfaces.surface_obb(self._native_surface)
        return Box(xh, yh, zh, frame=ax3_to_compas(frame))

    def intersections_with_line(self, line: Line) -> list[Point]:
        """Compute the intersections with a line."""
        points = _surfaces.surface_intersections_with_line(self._native_surface, list(line.start), list(line.direction))
        return [point_to_compas(p) for p in points]

    def intersections_with_curve(self, curve: OCCCurve) -> list[Point]:
        """Compute the intersections with a curve."""
        points = _surfaces.surface_intersections_with_curve(self._native_surface, curve.occ_curve)
        return [point_to_compas(p) for p in points]
