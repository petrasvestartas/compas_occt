import pathlib
from typing import Optional
from typing import Union

import compas.datastructures
import compas.geometry
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Polyline
from compas.geometry import Translation
from compas.geometry import Vector
from compas.geometry import is_point_behind_plane
from compas.tolerance import TOL
from compas_occt import _occt as _brep
from compas_occt import _occt as _io
from compas_occt import _occt as _meshing
from compas_occt.conversions import aabb_to_compas
from compas_occt.conversions import compas_transformation_to_trsf
from compas_occt.conversions import frame_to_occ_ax2
from compas_occt.conversions import location_to_compas
from compas_occt.conversions import ngon_to_face
from compas_occt.conversions import obb_to_compas
from compas_occt.conversions import point_to_compas
from compas_occt.conversions import quad_to_face
from compas_occt.conversions import triangle_to_face
from compas_occt.conversions import vector_to_occ
from compas_occt.geometry import OCCCurve
from compas_occt.geometry import OCCNurbsSurface
from compas_occt.geometry import OCCSurface
from compas_occt.occ import COMPOUND
from compas_occt.occ import COMPSOLID
from compas_occt.occ import SHELL
from compas_occt.occ import SOLID
from compas_occt.occ import compute_shape_centreofmass
from compas_occt.occ import split_shapes

from .brepedge import OCCBrepEdge
from .brepface import OCCBrepFace
from .breploop import OCCBrepLoop
from .brepvertex import OCCBrepVertex
from .errors import BrepBooleanError
from .errors import BrepFilletError


def _shape_list(items) -> list:
    if isinstance(items, list):
        return [item.native_brep for item in items]
    return [items.native_brep]


class OCCBrep(Brep):
    """
    Class for Boundary Representation of geometric entities.

    Attributes
    ----------
    vertices
        The vertices of the Brep.
    edges
        The edges of the Brep.
    loops
        The loops of the Brep.
    faces
        The faces of the Brep.
    frame
        The local coordinate system of the Brep.
    area
        The surface area of the Brep.
    volume
        The volume of the regions contained by the Brep.

    """

    @property
    def __data__(self) -> dict:
        return {
            "vertices": [vertex.__data__ for vertex in self.vertices],
            "edges": [edge.__data__ for edge in self.edges],
            "faces": [face.__data__ for face in self.faces],
        }

    @classmethod
    def __from_data__(cls, data: dict) -> "OCCBrep":
        """Construct an OCCBrep from its data representation.

        Parameters
        ----------
        data
            The data dictionary.

        Returns
        -------
        OCCBrep

        """
        from .builder import OCCBrepBuilder

        builder = OCCBrepBuilder()
        brep = builder.build(data["faces"])
        return brep

    def __init__(self) -> None:
        super().__init__()
        self._vertices = None
        self._edges = None
        self._loops = None
        self._faces = None
        self._shells = None
        self._solids = None

        self._aabb = None
        self._obb = None
        self._area = None
        self._volume = None
        self._centroid = None

    def copy(self) -> "OCCBrep":
        """Deep-copy this BRep using the native OCC copying mechanism.

        Returns
        -------
        OCCBrep

        """
        return OCCBrep.from_native(_brep.copy(self.occ_shape))

    # ==============================================================================
    # Customization
    # ==============================================================================

    # ==============================================================================
    # OCC Properties
    # ==============================================================================

    @property
    def occ_shape(self):
        return self._occ_shape

    @occ_shape.setter
    def occ_shape(self, shape) -> None:
        self._occ_shape = shape
        self._vertices = None
        self._edges = None
        self._loops = None
        self._faces = None
        self._shells = None
        self._solids = None

    @property
    def native_brep(self):
        return self.occ_shape

    @native_brep.setter
    def native_brep(self, shape) -> None:
        self.occ_shape = shape

    @property
    def orientation(self):
        return _brep.shape_orientation(self.occ_shape)

    # ==============================================================================
    # Properties
    # ==============================================================================

    @property
    def type(self) -> int:
        return _brep.shape_type(self.occ_shape)

    @property
    def is_shell(self):
        return self.type == SHELL

    @property
    def is_solid(self):
        return self.type == SOLID

    @property
    def is_compound(self):
        return self.type == COMPOUND

    @property
    def is_compoundsolid(self):
        return self.type == COMPSOLID

    @property
    def is_orientable(self) -> bool:
        return _brep.is_orientable(self.occ_shape)

    @property
    def is_closed(self) -> bool:
        return _brep.is_closed(self.occ_shape)

    @property
    def is_infinite(self) -> bool:
        return _brep.is_infinite(self.occ_shape)

    @property
    def is_convex(self) -> bool:
        return _brep.is_convex(self.occ_shape)

    @property
    def is_manifold(self) -> bool:
        return False

    @property
    def is_surface(self) -> bool:
        return False

    # ==============================================================================
    # Geometric Components
    # ==============================================================================

    @property
    def points(self) -> list[Point]:
        points = []
        seen = []
        for vertex in self.vertices:
            if any(vertex.is_same(test) for test in seen):
                continue
            seen.append(vertex)
            points.append(vertex.point)
        return points

    @property
    def curves(self) -> list[OCCCurve]:
        curves = []
        for edge in self.edges:
            curves.append(edge.curve)
        return curves

    @property
    def surfaces(self) -> list[OCCSurface]:
        surfaces = []
        for face in self.faces:
            surfaces.append(face.surface)
        return surfaces

    # ==============================================================================
    # Topological Components
    # ==============================================================================

    @property
    def vertices(self) -> list[OCCBrepVertex]:
        if self._vertices is None:
            self._vertices = [OCCBrepVertex(vertex) for vertex in _brep.shape_explore(self.occ_shape, 7)]
        return self._vertices

    @property
    def edges(self) -> list[OCCBrepEdge]:
        if self._edges is None:
            self._edges = [OCCBrepEdge(edge) for edge in _brep.shape_explore(self.occ_shape, 6)]
        return self._edges

    @property
    def loops(self) -> list[OCCBrepLoop]:
        if self._loops is None:
            self._loops = [OCCBrepLoop(wire) for wire in _brep.shape_explore(self.occ_shape, 5)]
        return self._loops

    @property
    def faces(self) -> list[OCCBrepFace]:
        if self._faces is None:
            self._faces = [OCCBrepFace(face) for face in _brep.shape_explore(self.occ_shape, 4)]
        return self._faces

    @property
    def shells(self) -> list["OCCBrep"]:
        if self._shells is None:
            self._shells = [OCCBrep.from_native(shell) for shell in _brep.shape_explore(self.occ_shape, 3)]
        return self._shells

    @property
    def solids(self) -> list["OCCBrep"]:
        if self._solids is None:
            self._solids = [OCCBrep.from_native(solid) for solid in _brep.shape_explore(self.occ_shape, 2)]
        return self._solids

    # ==============================================================================
    # Geometric Properties
    # ==============================================================================

    @property
    def frame(self) -> Frame:
        return location_to_compas(_brep.location_frame(self.occ_shape))

    @property
    def area(self) -> float:
        self._area = _brep.area(self.native_brep)
        return self._area

    @property
    def volume(self) -> float:
        self._volume = _brep.volume(self.occ_shape)
        return self._volume

    @property
    def centroid(self) -> Point:
        self._centroid = point_to_compas(_brep.centroid(self.occ_shape))
        return self._centroid

    @property
    def aabb(self) -> Box:
        return aabb_to_compas(_brep.aabb(self.native_brep, False))

    @property
    def obb(self) -> Box:
        return obb_to_compas(_brep.obb(self.native_brep))

    @property
    def convex_hull(self) -> Mesh:
        raise NotImplementedError

    # ==============================================================================
    # Read/Write
    # ==============================================================================

    @classmethod
    def from_step(
        cls,
        filename: Union[str, pathlib.Path],
        heal: bool = False,
        solid: bool = False,
    ) -> "OCCBrep":
        """
        Conctruct a BRep from the data contained in a STEP file.

        Parameters
        ----------
        filename
            The file.
        solid
            If True, convert shells to solids when possible.

        Returns
        -------
        OCCBrep

        """
        shape = _io.read_step(str(filename))
        brep = cls.from_native(shape)
        if heal:
            brep.heal()
        if solid:
            brep.make_solid()
        return brep

    @classmethod
    def from_step_with_attributes(cls, filename: Union[str, pathlib.Path]) -> list[tuple["OCCBrep", str, dict]]:
        """Read a STEP file together with the name and attributes of each top-level shape.

        Parameters
        ----------
        filename
            The file.

        Returns
        -------
        list[tuple[OCCBrep, str, dict]]
            For every free shape in the file: the Brep, its name, and a dict with its
            string, integer, and real attributes (see :meth:`to_step_with_attributes`).

        """
        records = _io.read_step_with_attributes(str(filename))
        return [(cls.from_native(shape), name, {**strings, **integers, **reals}) for shape, name, strings, integers, reals in records]

    def to_step_with_attributes(
        self,
        filepath: Union[str, pathlib.Path],
        name: Optional[str] = None,
        attributes: Optional[dict] = None,
    ) -> None:
        """Write the BRep to a STEP file with a name and custom attributes.

        The attributes are stored as user-defined properties (``general_property``
        entities) following the OCCT extended data exchange (XDE) conventions.

        Parameters
        ----------
        filepath
            Location of the file.
        name
            The name of the shape in the STEP file.
        attributes
            A mapping of attribute names to ``str``, ``int``, or ``float`` values.

        Returns
        -------
        None

        """
        strings: dict[str, str] = {}
        integers: dict[str, int] = {}
        reals: dict[str, float] = {}
        for key, value in (attributes or {}).items():
            if isinstance(value, bool):
                integers[key] = int(value)
            elif isinstance(value, int):
                integers[key] = value
            elif isinstance(value, float):
                reals[key] = value
            else:
                strings[key] = str(value)
        _io.write_step_with_attributes(self.occ_shape, str(filepath), name or self.name or "", strings, integers, reals)

    @classmethod
    def from_iges(cls, filename: Union[str, pathlib.Path], solid: bool = True) -> "OCCBrep":
        """
        Conctruct a BRep from the data contained in a IGES file.

        Parameters
        ----------
        filename
            The file.
        solid
            If True, convert shells to solids when possible.

        Returns
        -------
        OCCBrep

        """
        shape = _io.read_iges(str(filename))
        brep = cls.from_native(shape)
        brep.heal()
        if solid:
            brep.make_solid()
        return brep

    def to_brep(
        self,
        filepath: Union[str, pathlib.Path],
    ) -> None:
        """
        Write the BRep shape to a BREP file.

        Parameters
        ----------
        filepath
            Location of the file.

        Returns
        -------
        None

        """
        _io.write_brep(self.native_brep, str(filepath))

    def to_step(
        self,
        filepath: Union[str, pathlib.Path],
        unit: str = "MM",
        author: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        organization: Optional[str] = None,
    ) -> None:
        """
        Write the BRep shape to a STEP file.

        Parameters
        ----------
        filepath
            Location of the file.
        unit
            Base units for the geometry in the file.

        Returns
        -------
        None

        """
        _io.write_step(
            self.occ_shape,
            str(filepath),
            unit,
            name or self.name or "",
            author or "",
            organization or "",
            description or "",
        )

    def to_stl(
        self,
        filepath: Union[str, pathlib.Path],
        linear_deflection: float = 1e-3,
        angular_deflection: float = 0.5,
    ) -> bool:
        """
        Write the BRep shape to a STL file.

        Parameters
        ----------
        filepath
            Location of the file.
        linear_deflection
            Allowable deviation between curved geometry and mesh discretisation.
        angular_deflection
            Maximum angle between two adjacent facets.

        Returns
        -------
        None

        """
        return _io.write_stl(self.occ_shape, str(filepath), linear_deflection, angular_deflection)

    def to_iges(self, filepath: Union[str, pathlib.Path]) -> bool:
        """
        Write the BRep shape to a IGES file.

        Parameters
        ----------
        filepath
            Location of the file.

        Returns
        -------
        None

        """
        return _io.write_iges(self.occ_shape, str(filepath))

    # ==============================================================================
    # Constructors
    # ==============================================================================

    @classmethod
    def from_box(cls, box: compas.geometry.Box) -> "OCCBrep":
        """
        Construct a BRep from a COMPAS box.

        Parameters
        ----------
        box

        Returns
        -------
        OCCBrep

        """
        xaxis = box.frame.xaxis.scaled(-0.5 * box.xsize)
        yaxis = box.frame.yaxis.scaled(-0.5 * box.ysize)
        zaxis = box.frame.zaxis.scaled(-0.5 * box.zsize)
        frame = box.frame.transformed(Translation.from_vector(xaxis + yaxis + zaxis))
        shape = _brep.make_box(frame_to_occ_ax2(frame), box.xsize, box.ysize, box.zsize)
        return cls.from_native(shape)

    @classmethod
    def from_brepfaces(cls, faces: list[OCCBrepFace], solid: bool = True) -> "OCCBrep":
        """
        Make a BRep from a list of BRep faces forming an open or closed shell.

        Parameters
        ----------
        faces
            The input faces.
        solid
            Flag indicating that if the resulting shape should be converted to a solid, if possible.

        Returns
        -------
        OCCBrep

        """
        occ_faces = []
        for face in faces:
            if not face.is_valid():
                face.fix()
            occ_faces.append(face.occ_face)
        shell = _brep.shell_from_faces(occ_faces)
        brep = cls.from_native(shell)
        brep.heal()
        if solid:
            brep.make_solid()
        return brep

    @classmethod
    def from_breps(cls, breps: list["OCCBrep"]) -> "OCCBrep":
        """
        Construct one compound BRep out of multiple individual BReps.
        """
        compound = _brep.compound_from_shapes([brep.native_brep for brep in breps])
        return cls.from_native(compound)

    @classmethod
    def from_cone(cls, cone: compas.geometry.Cone) -> "OCCBrep":
        """
        Construct a BRep from a COMPAS cone.

        Parameters
        ----------
        cone
            A COMPAS cone.

        Returns
        -------
        OCCBrep

        """
        raise NotImplementedError

    @classmethod
    def from_curves(cls, curves: list[compas.geometry.NurbsCurve]) -> "OCCBrep":
        """
        Construct a BRep from a set of curves.

        Parameters
        ----------
        curves
            The input curves.

        Returns
        -------
        OCCBrep
            The resulting BRep.

        """
        raise NotImplementedError

    @classmethod
    def from_cylinder(cls, cylinder: compas.geometry.Cylinder) -> "OCCBrep":
        """
        Construct a BRep from a COMPAS cylinder.

        Parameters
        ----------
        cylinder
            A COMPAS cylinder.

        Returns
        -------
        OCCBrep

        """
        height = cylinder.height
        radius = cylinder.radius
        frame = cylinder.frame
        shape = _brep.make_cylinder(frame_to_occ_ax2(frame), radius, height)
        return cls.from_native(shape)

    @classmethod
    def from_extrusion(
        cls,
        profile: Union[OCCBrepEdge, OCCBrepFace],
        vector: Vector,
        cap_ends: bool = False,
    ) -> "OCCBrep":
        """
        Construct a BRep by extruding a closed curve along a direction vector.

        Parameters
        ----------
        profile
            The base profile of the extrusion.
        vector
            The extrusion vector.
            The extrusion has the same height as the length vector.
        cap_ends
            Flag indicating that the ends of the brep should be capped.
            Currently this flag is not supported.

        Returns
        -------
        OCCBrep

        """
        if cap_ends:
            raise NotImplementedError

        brep = cls()
        brep.native_brep = _brep.make_prism(profile.occ_shape, vector_to_occ(vector))
        return brep

    @classmethod
    def from_loft(
        cls,
        curves: list[OCCCurve],
        start: Optional[Point] = None,
        end: Optional[Point] = None,
    ) -> "OCCBrep":
        """Construct a Brep by lofing through a sequence of curves.

        Parameters
        ----------
        curves
            The loft curves.
        start
            The start point of the loft.
        end
            The end point of the loft.

        Returns
        -------
        OCCBrep

        """
        if start or end:
            raise NotImplementedError
        wires = [OCCBrepLoop.from_edges([OCCBrepEdge.from_curve(curve)]).occ_wire for curve in curves]
        shape = _brep.make_thrusections(wires, False, False)
        return Brep.from_native(shape)

    @classmethod
    def from_mesh(cls, mesh: compas.datastructures.Mesh, solid: bool = True) -> "OCCBrep":
        """
        Construct a BRep from a COMPAS mesh.

        Parameters
        ----------
        mesh
            The input mesh.
        solid
            Flag indicating that if the resulting shape should be converted to a solid, if possible.

        Returns
        -------
        OCCBrep

        """
        faces = []
        for face in mesh.faces():
            points = mesh.face_polygon(face)
            if len(points) == 3:
                faces.append(triangle_to_face(points))
            elif len(points) == 4:
                faces.append(quad_to_face(points))
            else:
                faces.append(ngon_to_face(points))
        shell = _brep.shell_from_faces(faces)
        brep = cls.from_native(shell)
        brep.heal()
        if solid:
            brep.make_solid()
        return brep

    @classmethod
    def from_native(cls, shape) -> "OCCBrep":
        """
        Construct a BRep from an OCC shape.

        Parameters
        ----------
        shape
            The OCC shape.

        Returns
        -------
        OCCBrep

        """
        return cls.from_shape(shape)

    @classmethod
    def from_polygons(cls, polygons: list[compas.geometry.Polygon], solid: bool = True) -> "OCCBrep":
        """
        Construct a BRep from a set of polygons.

        Parameters
        ----------
        polygons
            The input polygons.
        solid
            Flag indicating that if the resulting shape should be converted to a solid, if possible.

        Returns
        -------
        OCCBrep

        """
        faces = []
        for points in polygons:
            if len(points) == 3:
                faces.append(triangle_to_face(points))
            elif len(points) == 4:
                faces.append(quad_to_face(points))
            else:
                faces.append(ngon_to_face(points))
        shell = _brep.shell_from_faces(faces)
        brep = cls.from_native(shell)
        brep.heal()
        if solid:
            brep.make_solid()
        return brep

    # @classmethod
    # def from_pipe(cls) -> "OCCBrep":
    #     pass

    @classmethod
    def from_plane(
        cls,
        plane: Plane,
        domain_u: tuple[float, float] = (-1.0, +1.0),
        domain_v: tuple[float, float] = (-1.0, +1.0),
    ) -> "OCCBrep":
        """
        Make a BRep from a plane.

        Parameters
        ----------
        plane
            A COMPAS plane.
        domain_u
            The domain of the plane in the U direction.
        domain_v
            The domain of the plane in the V direction.

        Returns
        -------
        OCCBrep

        """
        return cls.from_brepfaces([OCCBrepFace.from_plane(plane, domain_u=domain_u, domain_v=domain_v)])

    @classmethod
    def from_planes(cls, planes: list[Plane], solid: bool = True) -> "OCCBrep":
        """
        Make a BRep from a list of planes.

        Parameters
        ----------
        planes
            The input planes.
        solid
            Flag indicating that if the resulting shape should be converted to a solid, if possible.

        Returns
        -------
        OCCBrep

        """
        faces = []
        for plane in planes:
            faces.append(OCCBrepFace.from_plane(plane))
        return cls.from_brepfaces(faces, solid=solid)

    @classmethod
    def from_shape(cls, shape) -> "OCCBrep":
        """
        Construct a BRep from an OCC shape.

        Parameters
        ----------
        shape
            The OCC shape.

        Returns
        -------
        OCCBrep

        """
        brep = cls()
        brep.native_brep = shape
        return brep

    @classmethod
    def from_sphere(cls, sphere: compas.geometry.Sphere) -> "OCCBrep":
        """
        Construct a BRep from a COMPAS sphere.

        Parameters
        ----------
        sphere
            A COMPAS sphere.

        Returns
        -------
        OCCBrep

        """
        shape = _brep.make_sphere(list(sphere.frame.point), sphere.radius)
        return cls.from_native(shape)

    @classmethod
    def from_surface(
        cls,
        surface: Union[compas.geometry.Surface, OCCNurbsSurface],
        domain_u: Optional[tuple[float, float]] = None,
        domain_v: Optional[tuple[float, float]] = None,
        precision: float = 1e-6,
        loop: Optional[OCCBrepLoop] = None,
        inside: bool = True,
    ) -> "OCCBrep":
        """
        Construct a BRep from a COMPAS surface.

        Parameters
        ----------
        surface
            The input surface.
        domain_u
            The domain of the surface in the U direction.
        domain_v
            The domain of the surface in the V direction.
        precision
            The precision of the discretisation of the surface.
        loop
            The loop to trim the surface with.
        inside
            Whether to keep the inside or outside of the loop.

        Returns
        -------
        OCCBrep

        """
        face = OCCBrepFace.from_surface(
            surface,
            domain_u=domain_u,
            domain_v=domain_v,
            precision=precision,
            loop=loop,
            inside=inside,
        )
        return cls.from_brepfaces([face])

    @classmethod
    def from_sweep(
        cls,
        profile: Union[OCCBrepEdge, OCCBrepFace],
        path: OCCBrepLoop,
    ) -> "OCCBrep":
        """
        Construct a BRep by sweeping a profile along a path.

        References
        ----------
        https://dev.opencascade.org/doc/occt-7.4.0/refman/html/class_b_rep_prim_a_p_i___make_sweep.html
        https://dev.opencascade.org/doc/occt-7.4.0/refman/html/class_b_rep_offset_a_p_i___make_pipe.html
        https://dev.opencascade.org/doc/occt-7.4.0/refman/html/class_b_rep_offset_a_p_i___make_pipe_shell.html

        """
        brep = cls()
        brep.native_brep = _brep.make_pipe(path.occ_wire, profile.occ_shape)
        return brep

    @classmethod
    def from_torus(cls, torus: compas.geometry.Torus) -> "OCCBrep":
        """
        Construct a BRep from a COMPAS torus.

        Parameters
        ----------
        torus
            A COMPAS torus.

        Returns
        -------
        OCCBrep

        """
        frame = torus.frame
        shape = _brep.make_torus(frame_to_occ_ax2(frame), torus.radius_axis, torus.radius_pipe)
        return cls.from_native(shape)

    # create patch
    # create offset

    # ==============================================================================
    # Boolean Constructors
    # ==============================================================================

    @classmethod
    def from_boolean_difference(
        cls,
        A: Union["OCCBrep", list["OCCBrep"]],
        B: Union["OCCBrep", list["OCCBrep"]],
        tol=None,
    ) -> "OCCBrep":
        """
        Construct a BRep from the boolean difference of two other BReps.

        Parameters
        ----------
        A
            A OCCBrep or list of OCCBreps to subtract from.
        B
            A OCCBrep or list of OCCBreps to subtract.

        Returns
        -------
        OCCBrep

        """
        tol = tol or TOL.absolute
        shape = _brep.boolean_difference(_shape_list(A), _shape_list(B), tol)
        brep = cls.from_native(shape)
        brep.sew()
        brep.fix()
        brep.make_solid()
        return brep

    @classmethod
    def from_boolean_intersection(
        cls,
        A: Union["OCCBrep", list["OCCBrep"]],
        B: Union["OCCBrep", list["OCCBrep"]],
        tol=None,
    ) -> "OCCBrep":
        """
        Construct a BRep from the boolean intersection of two other BReps.

        Parameters
        ----------
        A
            A OCCBrep or list of OCCBreps.
        B
            A OCCBrep or list of OCCBreps.

        Returns
        -------
        OCCBrep

        Raises
        ------
        BrepBooleanError

        """
        tol = tol or TOL.absolute
        try:
            shape = _brep.boolean_intersection(_shape_list(A), _shape_list(B), tol)
        except RuntimeError as e:
            raise BrepBooleanError(str(e))
        brep = cls.from_native(shape)
        brep.heal()
        brep.make_solid()
        return brep

    @classmethod
    def from_boolean_union(
        cls,
        A: Union["OCCBrep", list["OCCBrep"]],
        B: Union["OCCBrep", list["OCCBrep"]],
        tol=None,
    ) -> "OCCBrep":
        """
        Construct a BRep from the boolean union of two other BReps.

        Parameters
        ----------
        A
            A OCCBrep or list of OCCBreps.
        B
            A OCCBrep or list of OCCBreps.

        Returns
        -------
        OCCBrep

        Raises
        ------
        BrepBooleanError

        """
        tol = tol or TOL.absolute
        try:
            shape = _brep.boolean_union(_shape_list(A), _shape_list(B), tol)
        except RuntimeError as e:
            raise BrepBooleanError(str(e))
        brep = cls.from_native(shape)
        brep.heal()
        brep.make_solid()
        return brep

    # ==============================================================================
    # Converters
    # ==============================================================================

    def to_tesselation(
        self,
        linear_deflection: Optional[float] = None,
        angular_deflection: Optional[float] = None,
    ) -> tuple[Mesh, list[Polyline]]:
        """
        Create a tesselation of the shape for visualisation.

        Parameters
        ----------
        linear_deflection
            Allowable "distance" deviation between curved geometry and mesh discretisation.
        angular_deflection
            Allowable "curvature" deviation between curved geometry and mesh discretisation.

        Returns
        -------
        tuple[Mesh, list[Polyline]]

        """
        linear_deflection = linear_deflection or TOL.lineardeflection
        angular_deflection = angular_deflection or TOL.angulardeflection

        vertices, triangles, edges = _meshing.tesselate(self.occ_shape, linear_deflection, angular_deflection)
        mesh = Mesh.from_vertices_and_faces(vertices, triangles)
        polylines = [Polyline([point_to_compas(point) for point in polyline]) for polyline in edges]
        return mesh, polylines

    def to_meshes(self, u: int = 16, v: int = 16) -> list[Mesh]:
        """
        Convert the faces of the BRep shape to meshes.

        Parameters
        ----------
        u
            The number of mesh faces in the U direction of the underlying surface geometry of every face of the Brep.
        v
            The number of mesh faces in the V direction of the underlying surface geometry of every face of the Brep.

        Returns
        -------
        list[Mesh]

        """
        brep = OCCBrep.from_shape(_brep.nurbsconvert(self.occ_shape))
        meshes = []
        for face in brep.faces:
            srf = OCCNurbsSurface.from_face(face.occ_face)
            mesh = srf.to_tesselation()
            meshes.append(mesh)
        return meshes

    def to_polygons(self) -> list[Polygon]:
        """
        Convert the faces of the BRep to simple polygons without underlying geometry.

        Returns
        -------
        list[Polygon]

        """
        polygons = []
        for face in self.faces:
            points = []
            for vertex in face.loops[0].vertices:
                points.append(vertex.point)
            polygons.append(Polygon(points))
        return polygons

    def to_viewmesh(
        self,
        linear_deflection: Optional[float] = None,
        angular_deflection: Optional[float] = None,
    ) -> tuple[compas.datastructures.Mesh, list[compas.geometry.Polyline]]:
        """
        Convert the BRep to a view mesh.

        Parameters
        ----------
        linear_deflection
            Allowable "distance" deviation between curved geometry and mesh discretisation.
        angular_deflection
            Allowable "curvature" deviation between curved geometry and mesh discretisation.

        Returns
        -------
        tuple[Mesh, list[Polyline]]
        """
        return self.to_tesselation(linear_deflection=linear_deflection, angular_deflection=angular_deflection)

    # ==============================================================================
    # Relationships
    # ==============================================================================

    def vertex_neighbors(self, vertex: OCCBrepVertex) -> list[OCCBrepVertex]:
        """
        Identify the neighbouring vertices of a given vertex.

        Parameters
        ----------
        vertex
            A vertex of the Brep.

        Returns
        -------
        list[OCCBrepVertex]
            The neighbouring vertices of the given vertex.

        """
        results = _brep.ancestors(self.occ_shape, vertex.occ_vertex, 7, 6)
        vertices = []
        for occ_edge in results:
            edge = OCCBrepEdge(occ_edge)
            if not _brep.shape_is_same(edge.first_vertex.occ_vertex, vertex.occ_vertex):
                vertices.append(edge.first_vertex)
            else:
                vertices.append(edge.last_vertex)
        return vertices

    def vertex_edges(self, vertex: OCCBrepVertex) -> list[OCCBrepEdge]:
        """
        Identify the edges connected to a given vertex.

        Parameters
        ----------
        vertex
            A vertex of the Brep

        Returns
        -------
        list[OCCBrepEdge]
            The edges connected to the given vertex.

        """
        return [OCCBrepEdge(edge) for edge in _brep.ancestors(self.occ_shape, vertex.occ_vertex, 7, 6)]

    def vertex_faces(self, vertex: OCCBrepVertex) -> list[OCCBrepFace]:
        """
        Identify the faces connected to a vertex.

        Parameters
        ----------
        vertex
            A vertex of the Brep.

        Returns
        -------
        list[OCCBrepFace]
            The faces connected to the given vertex.

        """
        return [OCCBrepFace(face) for face in _brep.ancestors(self.occ_shape, vertex.occ_vertex, 7, 4)]

    def edge_faces(self, edge: OCCBrepEdge) -> list[OCCBrepFace]:
        """
        Identify the faces connected to an edge.

        Parameters
        ----------
        edge
            An edge of the Brep.

        Returns
        -------
        list[OCCBrepFace]
            The faces connected to the given edge.

        """
        return [OCCBrepFace(face) for face in _brep.ancestors(self.occ_shape, edge.occ_edge, 6, 4)]

    def edge_loops(self, edge: OCCBrepEdge) -> list[OCCBrepLoop]:
        """Identify the parent loops of an edge.

        Parameters
        ----------
        edge
            An edge of the Brep.

        Returns
        -------
        list[OCCBrepLoop]
            The loops containing the given edge.

        """
        return [OCCBrepLoop(wire) for wire in _brep.ancestors(self.occ_shape, edge.occ_edge, 6, 5)]

    # ==============================================================================
    # Other Methods
    # ==============================================================================

    def boolean_difference(self, *others: "OCCBrep", tol=None) -> "OCCBrep":
        """Return the boolean difference of this shape and a collection of other shapes.

        Parameters
        ----------
        others
            A collection of other BRep shapes to subtract from the current shape.

        Results
        -------
        OCCBrep
            The difference between the current shape and the other shapes.

        Raises
        ------
        BrepBooleanError

        """
        tol = tol or TOL.absolute
        try:
            shape = _brep.boolean_difference([self.native_brep], [b.native_brep for b in others], tol)
        except RuntimeError as e:
            raise BrepBooleanError(str(e))
        cls = type(self)
        brep = cls.from_native(shape)
        brep.heal()
        brep.make_solid()
        return brep

    def boolean_intersection(self, *others: "OCCBrep", tol=None) -> "OCCBrep":
        """Return the boolean intersection of the current shape and a collection of other shapes.

        Parameters
        ----------
        others
            A collection of other BRep shapes to intersect with the current shape.

        Returns
        -------
        OCCBrep
            The intersection between the current shape and the others.

        Raises
        ------
        BrepBooleanError

        """
        tol = tol or TOL.absolute
        try:
            shape = _brep.boolean_intersection([self.native_brep], [b.native_brep for b in others], tol)
        except RuntimeError as e:
            raise BrepBooleanError(str(e))
        cls = type(self)
        brep = cls.from_native(shape)
        brep.heal()
        brep.make_solid()
        return brep

    def boolean_union(self, *others: "OCCBrep", tol=None) -> "OCCBrep":
        """Return the boolean union of the current shape and a collection of other shapes.

        Parameters
        ----------
        others
            A collection of other BRep shapes to unite with the current shape.

        Returns
        -------
        OCCBrep
            The union between the current shape and the others.

        Raises
        ------
        BrepBooleanError

        """
        tol = tol or TOL.absolute
        try:
            shape = _brep.boolean_union([self.native_brep], [b.native_brep for b in others], tol)
        except RuntimeError as e:
            raise BrepBooleanError(str(e))
        cls = type(self)
        brep = cls.from_native(shape)
        brep.heal()
        brep.make_solid()
        return brep

    def check(self):
        """
        Check the shape.

        Returns
        -------
        None

        """
        if self.type == SHELL:
            print(_brep.is_valid(self.occ_shape))

    def contours(self, planes: list[compas.geometry.Plane]) -> list[list[compas.geometry.Polyline]]:
        """
        Generate contour lines by slicing the BRep shape with a series of planes.

        Parameters
        ----------
        planes
            The slicing planes.

        Returns
        -------
        list[list[compas.geometry.Polyline]]
            A list of polylines per plane.

        """
        raise NotImplementedError

    def cull_unused_vertices(self) -> None:
        """
        Remove all unused vertices.

        Returns
        -------
        None

        """
        raise NotImplementedError

    def cull_unused_edges(self) -> None:
        """
        Remove all unused edges.

        Returns
        -------
        None

        """
        raise NotImplementedError

    def cull_unused_loops(self) -> None:
        """
        Remove all unused loops.

        Returns
        -------
        None

        """
        raise NotImplementedError

    def cull_unused_faces(self) -> None:
        """
        Remove all unused faces.

        Returns
        -------
        None

        """
        raise NotImplementedError

    def fillet(
        self,
        radius: float,
        exclude: Optional[list[OCCBrepEdge]] = None,
    ) -> None:
        """Fillet the edges of a BRep.

        Parameters
        ----------
        radius
            The radius of the fillet.
        exclude
            A list of edges to exclude from the fillet operation.

        Raises
        ------
        BrepFilletError
            If the fillet operation could not be completed.

        Returns
        -------
        None
            the Brep is modified in-place.

        """
        exclude_shapes = [edge.occ_edge for edge in exclude] if exclude else []
        try:
            self.occ_shape = _brep.fillet(self.occ_shape, radius, exclude_shapes)
        except RuntimeError as e:
            raise BrepFilletError(str(e))

    def filleted(self, radius: float, exclude: Optional[list[OCCBrepEdge]] = None) -> "OCCBrep":
        """Construct a copy of a Brep with filleted edges.

        Parameters
        ----------
        radius
            The radius of the fillet.
        exclude
            A list of edges to exclude from the fillet operation.

        Returns
        -------
        OCCBrep

        """
        brep = self.copy()
        brep.fillet(radius, exclude=exclude)
        return brep

    def fix(self):
        """
        Fix the shell.

        Returns
        -------
        None

        """
        if self.type == SHELL:
            self.occ_shape = _brep.fix_shell(self.occ_shape)

    def heal(self):
        """
        Heal the shape.

        Returns
        -------
        None

        """
        self.sew()
        self.fix()

    def intersect(self, other: "OCCBrep") -> Union["OCCBrep", None]:
        """Intersect this Brep with another.

        Parameters
        ----------
        other
            The other brep.

        Returns
        -------
        OCCBrep
            If it exists, the intersection is a curve
            that can be accessed via the edges of the returned brep.

        """
        try:
            occ_shape = _brep.section(self.occ_shape, other.occ_shape)
        except RuntimeError:
            return None
        return OCCBrep.from_native(occ_shape)

    def make_positive(self):
        """Make the volume of a closed brep positive if it is not.

        Returns
        -------
        None

        """
        if self.is_closed:
            if self.volume < 0.0:
                self.native_brep = _brep.shape_reversed(self.occ_shape)

    def make_solid(self):
        """
        Convert the current shape to a solid if it is a shell.

        Returns
        -------
        None

        """
        if self.type == SHELL:
            self.occ_shape = _brep.solid_from_shell(self.occ_shape)

    def overlap(
        self,
        other: "OCCBrep",
        linear_deflection: Optional[float] = None,
        angular_deflection: Optional[float] = None,
        tolerance: float = 0.0,
        relative: bool = False,
    ) -> tuple[list[OCCBrepFace], list[OCCBrepFace]]:
        """
        Compute the overlap between this BRep and another.

        Parameters
        ----------
        other
            The other brep.
        linear_deflection
            Maximum linear deflection for shape approximation.
        angular_deflection
            Maximum angular deflection for shape approximation.
        tolerance
            Allowable deviation between shapes.

        Other Parameters
        ----------------
        relative
            If True, linear deflection used for faces is the maximum linear deflection of their edges.

        Returns
        -------
        tuple[list[OCCBrepFace], list[OCCBrepFace]]

        """
        linear_deflection = linear_deflection or TOL.lineardeflection
        angular_deflection = angular_deflection or TOL.angulardeflection

        faces1, faces2 = _brep.overlap(
            self.native_brep,
            other.native_brep,
            linear_deflection,
            angular_deflection,
            relative,
            tolerance,
        )
        return [OCCBrepFace(face) for face in faces1], [OCCBrepFace(face) for face in faces2]

    def overlap_intersection(
        self,
        other: "OCCBrep",
        linear_deflection: Optional[float] = None,
        angular_deflection: Optional[float] = None,
        tolerance: float = 0.0,
        relative: bool = False,
    ) -> Union["OCCBrep", None]:
        """Compute the common (shared) region of the faces where this BRep overlaps another.

        :meth:`overlap` reports *which* faces of the two Breps coincide; this returns the actual
        common geometry between them (the boolean intersection of those overlapping faces).

        Parameters
        ----------
        other
            The other brep.

        Returns
        -------
        OCCBrep | None
            The common region, or None if the breps do not overlap.

        """
        faces1, faces2 = self.overlap(
            other,
            linear_deflection=linear_deflection,
            angular_deflection=angular_deflection,
            tolerance=tolerance,
            relative=relative,
        )
        if not faces1 or not faces2:
            return None
        shape = _brep.boolean_intersection(
            [face.occ_shape for face in faces1],
            [face.occ_shape for face in faces2],
            0.0,
        )
        brep = OCCBrep.from_native(shape)
        return brep if brep.faces else None

    def sew(self):
        """
        Sew together the individual parts of the shape.

        Returns
        -------
        None

        """
        if len(self.faces) > 1:
            self.occ_shape = _brep.sew(self.occ_shape)

    def simplify(
        self,
        merge_edges: bool = True,
        merge_faces: bool = True,
        lineardeflection: Optional[float] = None,
        angulardeflection: Optional[float] = None,
    ):
        """Simplify the shape by merging colinear edges and coplanar faces.

        Parameters
        ----------
        merge_edges
            Merge edges with the same underlying geometry.
        merge_faces
            Merge faces with the same underlying geometry.
        lineardeflection
            Default is `compas.tolerance.Tolerance.lineardeflection`.
        angulardeflection
            Default is `compas.tolerance.Tolerance.angulardeflection`.

        Returns
        -------
        None

        """
        if not merge_edges and not merge_faces:
            return

        lineardeflection = lineardeflection or TOL.lineardeflection
        angulardeflection = angulardeflection or TOL.angulardeflection

        self.native_brep = _brep.simplify(self.native_brep, merge_edges, merge_faces, lineardeflection, angulardeflection)

    def slice(self, plane: compas.geometry.Plane) -> Union["OCCBrep", None]:
        """Slice a BRep with a plane.

        Parameters
        ----------
        plane
            The slicing plane.

        Returns
        -------
        OCCBrep | None
            The resulting Brep slice or None if the plane does not intersect the Brep.

        """
        if isinstance(plane, Frame):
            plane = Plane.from_frame(plane)

        face = OCCBrepFace.from_plane(plane)
        try:
            occ_shape = _brep.section(self.occ_shape, face.occ_face)
        except RuntimeError:
            return None
        return OCCBrep.from_native(occ_shape)

    def split(self, other: "OCCBrep") -> list["OCCBrep"]:
        """Split a BRep using another BRep as splitter.

        Parameters
        ----------
        other
            Another brep.

        Returns
        -------
        list[OCCBrep]

        """
        results = _brep.split([self.occ_shape], [other.occ_shape])
        return [OCCBrep.from_shape(shape) for shape in results]

    def transform(self, matrix: compas.geometry.Transformation) -> None:
        """
        Transform this Brep.

        Parameters
        ----------
        matrix
            A transformation matrix.

        Returns
        -------
        None

        """
        self._occ_shape = _brep.transform(self.occ_shape, compas_transformation_to_trsf(matrix), True)

    def transformed(self, matrix: compas.geometry.Transformation) -> "OCCBrep":
        """
        Return a transformed copy of the Brep.

        Parameters
        ----------
        matrix
            A transformation matrix.

        Returns
        -------
        OCCBrep

        """
        shape = _brep.transform(self.occ_shape, compas_transformation_to_trsf(matrix), True)
        return OCCBrep.from_shape(shape)

    def trim(self, plane: compas.geometry.Plane) -> None:
        """Trim a Brep with a plane.

        Parameters
        ----------
        plane
            The slicing plane.

        Returns
        -------
        None

        """
        if isinstance(plane, Frame):
            plane = Plane.from_frame(plane)

        arguments = [self.occ_shape]
        tools = [OCCBrepFace.from_plane(plane).occ_shape]
        results = split_shapes(arguments, tools)

        occ_shape = None
        for test in results:
            point = compute_shape_centreofmass(test)
            if is_point_behind_plane(point, plane):
                occ_shape = test
                break
        if occ_shape:
            self.occ_shape = occ_shape

    def trimmed(self, plane: compas.geometry.Plane) -> "OCCBrep":
        """Construct a copy of a Brep trimmed with a plane.

        Parameters
        ----------
        plane
            The slicing plane.

        Returns
        -------
        OCCBrep

        """
        brep = self.copy()
        brep.trim(plane)
        return brep

    def offset(self, distance: float) -> "OCCBrep":
        """Construct a thickened copy of the brep.

        Parameters
        ----------
        distance
            The thickness in the form of an offset distance.

        Returns
        -------
        OCCBrep

        """
        return Brep.from_native(_brep.offset(self.native_brep, distance))
