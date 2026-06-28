from typing import Optional

import compas.geometry
from compas.geometry import BrepFace
from compas.geometry import Cone
from compas.geometry import Cylinder
from compas.geometry import Frame
from compas.geometry import NurbsSurface
from compas.geometry import Plane
from compas.geometry import Polygon
from compas.geometry import Sphere
from compas.geometry import SurfaceType
from compas.geometry import Torus
from compas_occt import _occt as _brep
from compas_occt.brep import OCCBrepEdge
from compas_occt.brep import OCCBrepLoop
from compas_occt.brep import OCCBrepVertex
from compas_occt.conversions import cone_to_occ
from compas_occt.conversions import cylinder_to_compas
from compas_occt.conversions import cylinder_to_occ
from compas_occt.conversions import plane_to_compas
from compas_occt.conversions import plane_to_occ
from compas_occt.conversions import point_to_compas
from compas_occt.conversions import sphere_to_compas
from compas_occt.conversions import sphere_to_occ
from compas_occt.conversions import torus_to_occ
from compas_occt.geometry import OCCNurbsSurface
from compas_occt.geometry import OCCSurface


class OCCBrepFace(BrepFace):
    """
    Class representing a face in the BRep of a geometric shape.

    Parameters
    ----------
    occ_face
        An OCC BRep face.

    Attributes
    ----------
    vertices
        List of BRep vertices.
    edges
        List of BRep edges.
    loops
        List of BRep loops.
    surface
        Surface geometry from the adaptor.

    """

    @property
    def __data__(self) -> dict:
        loops = []
        for loop in self.loops:
            edges = []
            for edge in loop.edges:
                edgedata = {
                    "type": edge.type,
                    "curve": edge.curve,
                    "domain": edge.domain,
                    "start": edge.first_vertex.point,
                    "end": edge.last_vertex.point,
                    "orientation": edge.orientation,
                    "dimension": 3,
                }
                edges.append(edgedata)
            loops.append(edges)

        data = {
            "type": self.type,
            "surface": self.surface,
            "domain_u": self.domain_u,
            "domain_v": self.domain_v,
            "frame": Frame.worldXY(),
            "loops": loops,
            "orientation": self.orientation,
        }
        return data

    @classmethod
    def __from_data__(cls, data: dict) -> "OCCBrepFace":
        """Construct an object of this type from the provided data.

        Parameters
        ----------
        data
            The data dictionary.

        Returns
        -------
        OCCBrepFace
            An instance of this object type if the data contained in the dict has the correct schema.

        """
        raise NotImplementedError

    def __init__(self, occ_face):
        super().__init__()
        self.precision = 1e-6
        self._surface = None
        self._nurbssurface = None
        self._domain = None
        self._occ_face = occ_face

    def __eq__(self, other: "OCCBrepFace") -> bool:
        return self.is_equal(other)

    def is_same(self, other: "OCCBrepFace") -> bool:
        """Check if this face is the same as another face.

        Two faces are the same if they have the same location.

        Parameters
        ----------
        other
            The other face.

        Returns
        -------
        bool
            ``True`` if the faces are the same, ``False`` otherwise.

        """
        if not isinstance(other, OCCBrepFace):
            return False
        return _brep.shape_is_same(self.occ_face, other.occ_face)

    def is_equal(self, other: "OCCBrepFace") -> bool:
        """Check if this face is equal to another face.

        Two faces are equal if they have the same location and orientation.

        Parameters
        ----------
        other
            The other face.

        Returns
        -------
        bool
            ``True`` if the faces are equal, ``False`` otherwise.

        """
        if not isinstance(other, OCCBrepFace):
            return False
        return _brep.shape_is_equal(self.occ_face, other.occ_face)

    # ==============================================================================
    # OCC Properties
    # ==============================================================================

    @property
    def occ_shape(self):
        return self.occ_face

    @property
    def occ_face(self):
        return self._occ_face

    @occ_face.setter
    def occ_face(self, face) -> None:
        self._surface = None
        self._nurbssurface = None
        self._domain = None
        self._occ_face = face

    @property
    def orientation(self):
        return _brep.shape_orientation(self.occ_face)

    # remove this if possible
    @property
    def nurbssurface(self) -> OCCNurbsSurface:
        if not self._nurbssurface:
            self._nurbssurface = OCCNurbsSurface(_brep.face_to_bspline(self.occ_face))
        return self._nurbssurface

    @property
    def surface(self):
        if self.is_plane:
            return self.to_plane()
        if self.is_cylinder:
            return self.to_cylinder()
        if self.is_cone:
            return self.to_cone()
        if self.is_sphere:
            return self.to_sphere()
        if self.is_torus:
            return self.to_torus()
        if self.is_bspline:
            return self.to_nurbs()
        raise NotImplementedError

    # ==============================================================================
    # Properties
    # ==============================================================================

    @property
    def type(self) -> int:
        return _brep.face_type(self.occ_face)

    @property
    def is_plane(self) -> bool:
        return self.type == SurfaceType.PLANE

    @property
    def is_cylinder(self) -> bool:
        return self.type == SurfaceType.CYLINDER

    @property
    def is_sphere(self) -> bool:
        return self.type == SurfaceType.SPHERE

    @property
    def is_torus(self) -> bool:
        return self.type == SurfaceType.TORUS

    @property
    def is_cone(self) -> bool:
        return self.type == SurfaceType.CONE

    @property
    def is_bezier(self) -> bool:
        return self.type == SurfaceType.BEZIER_SURFACE

    @property
    def is_bspline(self) -> bool:
        return self.type == SurfaceType.BSPLINE_SURFACE

    # other types of surfaces:
    # -----------------------
    # revolved
    # extruded
    # offset
    # other

    @property
    def vertices(self) -> list[OCCBrepVertex]:
        return [OCCBrepVertex(vertex) for vertex in _brep.shape_explore(self.occ_face, 7)]

    @property
    def edges(self) -> list[OCCBrepEdge]:
        return [OCCBrepEdge(edge) for edge in _brep.shape_explore(self.occ_face, 6)]

    @property
    def loops(self) -> list[OCCBrepLoop]:
        return [OCCBrepLoop(wire) for wire in _brep.shape_explore(self.occ_face, 5)]

    @property
    def outerloop(self) -> OCCBrepLoop:
        return OCCBrepLoop(_brep.outer_wire(self.occ_face))

    @property
    def innerloops(self) -> list[OCCBrepLoop]:
        outerloop = self.outerloop
        inner = []
        for loop in self.loops:
            if not loop.is_same(outerloop):
                inner.append(loop)
        return inner

    @property
    def area(self) -> float:
        return _brep.area(self.occ_shape)

    @property
    def centroid(self) -> compas.geometry.Point:
        return point_to_compas(_brep.centroid(self.occ_shape))

    @property
    def domain_u(self) -> tuple[float, float]:
        if self._domain is None:
            self._domain = _brep.face_domain(self.occ_face)
        umin, umax, _, _ = self._domain
        return umin, umax

    @property
    def domain_v(self) -> tuple[float, float]:
        if self._domain is None:
            self._domain = _brep.face_domain(self.occ_face)
        _, _, vmin, vmax = self._domain
        return vmin, vmax

    # ==============================================================================
    # Constructors
    # ==============================================================================

    @classmethod
    def from_polygon(cls, points: Polygon) -> "OCCBrepFace":
        """
        Construct a BRep face from a polygon.

        Parameters
        ----------
        polygon

        Returns
        -------
        OCCBrepFace

        """
        return cls(_brep.make_face_polygon([list(point) for point in points]))

    @classmethod
    def from_plane(
        cls,
        plane: Plane,
        domain_u: Optional[tuple[float, float]] = None,
        domain_v: Optional[tuple[float, float]] = None,
        loop: Optional[OCCBrepLoop] = None,
        inside: bool = True,
    ) -> "OCCBrepFace":
        """
        Construct a face from a plane.

        Parameters
        ----------
        plane
            The plane.
        domain_u : tuple[float, float], optional
            U parameter minimum and maximum.
        domain_v : tuple[float, float], optional
            V parameter minimum and maximum.
        loop, optional
            A boundary loop.
        inside : bool, optional
            If True, the face is inside the boundary loop.

        Returns
        -------
        OCCBrepFace

        """
        domain = None
        if domain_u and domain_v:
            domain = [domain_u[0], domain_u[1], domain_v[0], domain_v[1]]
        loop_shape = loop.occ_wire if loop else None
        return cls(_brep.make_face_plane(plane_to_occ(plane), domain=domain, loop=loop_shape, inside=inside))

    @classmethod
    def from_cylinder(
        cls,
        cylinder: Cylinder,
        loop: Optional[OCCBrepLoop] = None,
        inside: bool = True,
    ) -> "OCCBrepFace":
        """
        Construct a face from a cylinder.

        Parameters
        ----------
        cylinder
            The cylinder.
        loop, optional
            A boundary loop.
        inside : bool, optional
            If True, the face is inside the boundary loop.

        Returns
        -------
        OCCBrepFace

        """
        loop_shape = loop.occ_wire if loop else None
        return cls(_brep.make_face_cylinder(cylinder_to_occ(cylinder), loop=loop_shape, inside=inside))

    @classmethod
    def from_cone(
        cls,
        cone: Cone,
        loop: Optional[OCCBrepLoop] = None,
        inside: bool = True,
    ) -> "OCCBrepFace":
        """
        Construct a face from a cone.

        Parameters
        ----------
        cone
            The cone.
        loop, optional
            A boundary loop.
        inside : bool, optional
            If True, the face is inside the boundary loop.

        Returns
        -------
        OCCBrepFace

        """
        loop_shape = loop.occ_wire if loop else None
        return cls(_brep.make_face_cone(cone_to_occ(cone), loop=loop_shape, inside=inside))

    @classmethod
    def from_sphere(
        cls,
        sphere: Sphere,
        loop: Optional[OCCBrepLoop] = None,
        inside: bool = True,
    ) -> "OCCBrepFace":
        """
        Construct a face from a sphere.

        Parameters
        ----------
        sphere
            The sphere.
        loop, optional
            A boundary loop.
        inside : bool, optional
            If True, the face is inside the boundary loop.

        Returns
        -------
        OCCBrepFace

        """
        loop_shape = loop.occ_wire if loop else None
        return cls(_brep.make_face_sphere(sphere_to_occ(sphere), loop=loop_shape, inside=inside))

    @classmethod
    def from_torus(
        cls,
        torus: Torus,
        loop: Optional[OCCBrepLoop] = None,
        inside: bool = True,
    ) -> "OCCBrepFace":
        """
        Construct a face from a torus.

        Parameters
        ----------
        torus
            The torus.
        loop, optional
            A boundary loop.
        inside : bool, optional
            If True, the face is inside the boundary loop.

        Returns
        -------
        OCCBrepFace

        """
        loop_shape = loop.occ_wire if loop else None
        return cls(_brep.make_face_torus(torus_to_occ(torus), loop=loop_shape, inside=inside))

    @classmethod
    def from_surface(
        cls,
        surface: OCCSurface,
        domain_u: Optional[tuple[float, float]] = None,
        domain_v: Optional[tuple[float, float]] = None,
        precision: float = 1e-6,
        loop: Optional[OCCBrepLoop] = None,
        inside: bool = True,
    ) -> "OCCBrepFace":
        """
        Construct a face from a surface.

        Parameters
        ----------
        surface
            The torus.
        domain_u
            U parameter minimum and maximum.
        domain_v
            V parameter minimum and maximum.
        precision
            Precision for face construction.
        loop
            A boundary loop.
        inside
            If True, the face is inside the boundary loop.

        Returns
        -------
        OCCBrepFace

        """
        domain = None
        if domain_u and domain_v:
            domain = [domain_u[0], domain_u[1], domain_v[0], domain_v[1]]
        loop_shape = loop.occ_wire if loop else None
        face = cls(_brep.make_face_surface(surface.occ_surface, domain=domain, precision=precision, loop=loop_shape, inside=inside))
        face.precision = precision
        return face

    # ==============================================================================
    # Conversions
    # ==============================================================================

    def to_polygon(self) -> Polygon:
        """
        Convert the face to a polygon without underlying geometry.

        Returns
        -------
        Polygon

        """
        return self.outerloop.to_polygon()

    def to_polygons(self) -> list[Polygon]:
        """
        Convert the face to polygons without underlying geometry.

        Returns
        -------
        list[Polygon]

        """
        return [loop.to_polygon() for loop in self.loops]

    def to_plane(self) -> Plane:
        """
        Convert the face surface geometry to a plane.

        Returns
        -------
        Plane

        """
        if not self.is_plane:
            raise Exception("Face is not a plane.")

        return plane_to_compas(_brep.face_to_plane(self.occ_face))

    def to_cylinder(self) -> Cylinder:
        """
        Convert the face surface geometry to a cylinder.

        Returns
        -------
        Cylinder

        """
        if not self.is_cylinder:
            raise Exception("Face is not a cylinder.")

        return cylinder_to_compas(_brep.face_to_cylinder(self.occ_face))

    def to_cone(self) -> Cone:
        """
        Convert the face surface geometry to a cone.

        Returns
        -------
        Cone

        """
        raise NotImplementedError

    def to_sphere(self) -> Sphere:
        """
        Convert the face surface geometry to a sphere.

        Returns
        -------
        Sphere

        """
        if not self.is_sphere:
            raise Exception("Face is not a sphere.")

        return sphere_to_compas(_brep.face_to_sphere(self.occ_face))

    def to_torus(self) -> Torus:
        """
        Convert the face surface geometry to a torus.

        Returns
        -------
        Torus

        """
        raise NotImplementedError

    def to_nurbs(self) -> NurbsSurface:
        """
        Convert the face surface geometry to a torus.

        Returns
        -------
        NurbsSurface

        """
        if not self.is_bspline:
            raise Exception("Face is not a nurbs surface.")

        return NurbsSurface.from_native(_brep.face_to_bspline(self.occ_face))

    # ==============================================================================
    # Methods
    # ==============================================================================

    def try_get_nurbssurface(
        self,
        precision=1e-3,
        continuity_u=None,
        continuity_v=None,
        maxdegree_u=5,
        maxdegree_v=5,
        maxsegments_u=1,
        maxsegments_v=1,
    ) -> OCCNurbsSurface:
        """
        Try to convert the underlying geometry to a Nurbs surface.

        """
        return OCCNurbsSurface(_brep.face_to_bspline(self.occ_face))

    def is_valid(self) -> bool:
        """
        Verify that the face is valid.

        Returns
        -------
        bool

        """
        return _brep.is_valid(self.occ_face)

    def fix(self) -> None:
        """
        Try to fix the face.

        Returns
        -------
        None

        """
        self.occ_face = _brep.fix_face(self.occ_face)

    def add_loop(self, loop: OCCBrepLoop, reverse: bool = False) -> None:
        """
        Add an inner loop to the face.

        Parameters
        ----------
        loop
            The additional loop.

        Returns
        -------
        None

        """
        self.occ_face = _brep.face_add_loop(self.occ_face, loop.occ_wire, reverse)

    def add_loops(self, loops: list[OCCBrepLoop], reverse: bool = False) -> None:
        """
        Add an inner loop to the face.

        Parameters
        ----------
        loops
            The additional loops.

        Returns
        -------
        None

        """
        for loop in loops:
            self.occ_face = _brep.face_add_loop(self.occ_face, loop.occ_wire, reverse)
