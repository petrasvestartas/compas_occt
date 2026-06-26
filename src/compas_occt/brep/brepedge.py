from typing import Optional

from compas.geometry import Bezier
from compas.geometry import BrepEdge
from compas.geometry import Circle
from compas.geometry import Ellipse
from compas.geometry import Hyperbola
from compas.geometry import Line
from compas.geometry import NurbsCurve
from compas.geometry import Parabola
from compas.geometry import Point
from compas_occt import _occt as _brep
from compas_occt.brep import OCCBrepVertex
from compas_occt.conversions import bezier_to_compas
from compas_occt.conversions import bspline_to_compas
from compas_occt.conversions import circle_to_compas
from compas_occt.conversions import circle_to_occ
from compas_occt.conversions import ellipse_to_compas
from compas_occt.conversions import hyperbola_to_compas
from compas_occt.conversions import line_to_occ
from compas_occt.conversions import parabola_to_compas
from compas_occt.conversions import point_to_occ
from compas_occt.geometry import OCCCurve
from compas_occt.geometry import OCCCurve2d
from compas_occt.geometry import OCCSurface


class CurveType:
    LINE = 0
    CIRCLE = 1
    ELLIPSE = 2
    HYPERBOLA = 3
    PARABOLA = 4
    BEZIER = 5
    BSPLINE = 6
    OTHER = 7
    CURVE2D = 8


class OCCBrepEdge(BrepEdge):
    """Class representing an edge in the BRep of a geometric shape.

    Parameters
    ----------
    occ_edge : TopoDS_Edge
        An OCC BRep edge.

    Attributes
    ----------
    curve
        Curve geometry from the edge adaptor.
    first_vertex
        The first vertex with forward orientation.
    is_line
        True if the underlying curve is a line.
    is_circle
        True if the underlying curve is a circle.
    is_ellipse
        True if the underlying curve is an ellipse.
    is_hyperbola
        True if the underlying curve is a hyperbola.
    is_parabola
        True if the underlying curve is a parabola.
    is_bezier
        True if the underlying curve is a bezier curve.
    is_bspline
        True if the underlying curve is a bspline curve.
    is_other
        True if the underlying curve is an other type of curve.
    last_vertex
        The first vertex with reversed orientation.
    vertices
        The topological vertices of the edge.
    type
        The type of the geometric curve underlying the topological edge.

    """

    @property
    def __data__(self) -> dict:
        return {"vertices": [self.first_vertex.__data__, self.last_vertex.__data__]}

    @classmethod
    def __from_data__(cls, data: dict) -> "OCCBrepEdge":
        raise NotImplementedError

    def __init__(self, occ_edge) -> None:
        super().__init__()
        self._occ_edge = occ_edge
        self.is_2d = False

    def __eq__(self, other: "OCCBrepEdge") -> bool:
        return self.is_equal(other)

    def is_same(self, other: "OCCBrepEdge") -> bool:
        """Check if this edge is the same as another edge.

        Two edges are the same if they have the same location.

        Parameters
        ----------
        other
            The other edge.

        Returns
        -------
        bool
            ``True`` if the edges are the same, ``False`` otherwise.

        """
        if not isinstance(other, OCCBrepEdge):
            return False
        return _brep.shape_is_same(self.occ_edge, other.occ_edge)

    def is_equal(self, other: "OCCBrepEdge") -> bool:
        """Check if this edge is equal to another edge.

        Two edges are equal if they have the same location and orientation.

        Parameters
        ----------
        other
            The other edge.

        Returns
        -------
        bool
            ``True`` if the edges are equal, ``False`` otherwise.

        """
        if not isinstance(other, OCCBrepEdge):
            return False
        return _brep.shape_is_equal(self.occ_edge, other.occ_edge)

    # ==============================================================================
    # OCC Properties
    # ==============================================================================

    @property
    def occ_shape(self):
        return self.occ_edge

    @property
    def occ_edge(self):
        return self._occ_edge

    @occ_edge.setter
    def occ_edge(self, edge) -> None:
        self._occ_edge = edge

    @property
    def orientation(self):
        return _brep.shape_orientation(self.occ_edge)

    @property
    def curve(self):
        if self.is_line:
            return self.to_line()
        if self.is_circle:
            return self.to_circle()
        if self.is_ellipse:
            return self.to_ellipse()
        if self.is_hyperbola:
            return self.to_hyperbola()
        if self.is_parabola:
            return self.to_parabola()
        if self.is_bezier:
            return self.to_bezier()
        if self.is_bspline:
            return self.to_bspline()
        raise NotImplementedError

    # ==============================================================================
    # Properties
    # ==============================================================================

    @property
    def type(self) -> int:
        return _brep.edge_type(self.occ_edge)

    @property
    def is_curve2d(self) -> bool:
        return self.type == CurveType.CURVE2D

    @property
    def is_line(self) -> bool:
        return self.type == CurveType.LINE

    @property
    def is_circle(self) -> bool:
        return self.type == CurveType.CIRCLE

    @property
    def is_ellipse(self) -> bool:
        return self.type == CurveType.ELLIPSE

    @property
    def is_hyperbola(self) -> bool:
        return self.type == CurveType.HYPERBOLA

    @property
    def is_parabola(self) -> bool:
        return self.type == CurveType.PARABOLA

    @property
    def is_bezier(self) -> bool:
        return self.type == CurveType.BEZIER

    @property
    def is_bspline(self) -> bool:
        return self.type == CurveType.BSPLINE

    @property
    def is_other(self) -> bool:
        return self.type == CurveType.OTHER

    @property
    def is_valid(self) -> bool:
        return _brep.is_valid(self.occ_edge)

    @property
    def vertices(self) -> list[OCCBrepVertex]:
        return [OCCBrepVertex(vertex) for vertex in _brep.shape_explore(self.occ_edge, 7)]

    @property
    def first_vertex(self) -> OCCBrepVertex:
        return OCCBrepVertex(_brep.edge_first_vertex(self.occ_edge))

    @property
    def last_vertex(self) -> OCCBrepVertex:
        return OCCBrepVertex(_brep.edge_last_vertex(self.occ_edge))

    @property
    def length(self) -> float:
        return _brep.edge_length(self.occ_edge)

    @property
    def domain(self) -> tuple[float, float]:
        return _brep.edge_domain(self.occ_edge)

    # ==============================================================================
    # Constructors
    # ==============================================================================

    @classmethod
    def from_vertex_vertex(cls, a: OCCBrepVertex, b: OCCBrepVertex) -> "OCCBrepEdge":
        """Construct an edge from two vertices.

        Parameters
        ----------
        a
            The first vertex.
        b
            The second vertex.

        Returns
        -------
        BrepEdge
            The constructed edge.

        """
        return cls(_brep.make_edge_vertex_vertex(a.occ_vertex, b.occ_vertex))

    @classmethod
    def from_point_point(cls, a: Point, b: Point) -> "OCCBrepEdge":
        """Construct an edge from two points.

        Parameters
        ----------
        a
            The first point.
        b
            The second point.

        Returns
        -------
        BrepEdge
            The constructed edge.

        """
        return cls(_brep.make_edge_point_point(point_to_occ(a), point_to_occ(b)))

    @classmethod
    def from_line(
        cls,
        line: Line,
        params: Optional[tuple[float, float]] = None,
        points: Optional[tuple[Point, Point]] = None,
        vertices: Optional[tuple[OCCBrepVertex, OCCBrepVertex]] = None,
    ) -> "OCCBrepEdge":
        """Construct an edge from a line.

        Parameters
        ----------
        line
            The line.
        params
            The parameters of the line.
        points
            The start and end points of the line.
        vertices
            The start and end vertices of the line.

        Returns
        -------
        BrepEdge
            The constructed edge.

        """
        points_data = (point_to_occ(points[0]), point_to_occ(points[1])) if points else None
        vertices_data = (vertices[0].occ_vertex, vertices[1].occ_vertex) if vertices else None
        return cls(_brep.make_edge_line(line_to_occ(line), params=params, points=points_data, vertices=vertices_data))

    @classmethod
    def from_circle(
        cls,
        circle: Circle,
        params: Optional[tuple[float, float]] = None,
        points: Optional[tuple[Point, Point]] = None,
        vertices: Optional[tuple[OCCBrepVertex, OCCBrepVertex]] = None,
    ) -> "OCCBrepEdge":
        """Construct an edge from a circle.

        Parameters
        ----------
        circle
            The circle.
        params
            The parameters of the circle.
        points
            The start and end points of the circle.
        vertices
            The start and end vertices of the circle.

        Returns
        -------
        BrepEdge
            The constructed edge.

        """
        points_data = (point_to_occ(points[0]), point_to_occ(points[1])) if points else None
        vertices_data = (vertices[0].occ_vertex, vertices[1].occ_vertex) if vertices else None
        return cls(_brep.make_edge_circle(circle_to_occ(circle), params=params, points=points_data, vertices=vertices_data))

    @classmethod
    def from_ellipse(cls, ellipse: Ellipse) -> "OCCBrepEdge":
        """Construct an edge from an ellipse.

        Parameters
        ----------
        ellipse
            The ellipse.

        Returns
        -------
        BrepEdge
            The constructed edge.

        """
        raise NotImplementedError

    @classmethod
    def from_curve(
        cls,
        curve: OCCCurve,
        params: Optional[tuple[float, float]] = None,
        points: Optional[tuple[Point, Point]] = None,
        vertices: Optional[tuple[OCCBrepVertex, OCCBrepVertex]] = None,
    ) -> "OCCBrepEdge":
        """Construct an edge from a curve.

        Parameters
        ----------
        curve
            The curve.
        params
            The parameters of the curve.
        points
            The start and end points of the curve.
        vertices
            The start and end vertices of the curve.

        Returns
        -------
        BrepEdge
            The constructed edge.

        """
        points_data = (point_to_occ(points[0]), point_to_occ(points[1])) if points else None
        vertices_data = (vertices[0].occ_vertex, vertices[1].occ_vertex) if vertices else None
        return cls(_brep.make_edge_curve(curve.occ_curve, params=params, points=points_data, vertices=vertices_data))

    @classmethod
    def from_curve_and_surface(
        cls,
        curve: OCCCurve,
        surface: OCCSurface,
        params: Optional[tuple[float, float]] = None,
        points: Optional[tuple[Point, Point]] = None,
        vertices: Optional[tuple[OCCBrepVertex, OCCBrepVertex]] = None,
    ) -> "OCCBrepEdge":
        """Construct an edge from a curve and a surface.

        The curve will be projected onto the surface and embedded into its parameter space automatically.

        Parameters
        ----------
        curve
            The curve.
        surface
            The surface.
        params
            The parameters of the curve.
        points
            The start and end points of the curve.
        vertices
            The start and end vertices of the curve.

        Returns
        -------
        BrepEdge
            The constructed edge.

        """
        curve2d = curve.projected(surface).embedded(surface)
        return cls.from_curve2d_and_surface(curve2d, surface, params=params, points=points, vertices=vertices)

    @classmethod
    def from_curve2d_and_surface(
        cls,
        curve2d: OCCCurve2d,
        surface: OCCSurface,
        params: Optional[tuple[float, float]] = None,
        points: Optional[tuple[Point, Point]] = None,
        vertices: Optional[tuple[OCCBrepVertex, OCCBrepVertex]] = None,
    ) -> "OCCBrepEdge":
        """Construct an edge from an embedded 2d curve and its embedding surface.

        Parameters
        ----------
        curve2d
            The 2D curve.
        surface
            The surface.
        params
            The parameters of the curve.
        points
            The start and end points of the curve.
        vertices
            The start and end vertices of the curve.

        Returns
        -------
        BrepEdge
            The constructed edge.

        """
        points_data = (point_to_occ(points[0]), point_to_occ(points[1])) if points else None
        vertices_data = (vertices[0].occ_vertex, vertices[1].occ_vertex) if vertices else None
        return cls(
            _brep.make_edge_curve2d_surface(
                curve2d.occ_curve,
                surface.occ_surface,
                params=params,
                points=points_data,
                vertices=vertices_data,
            )
        )

    # ==============================================================================
    # Conversions
    # ==============================================================================

    def to_line(self) -> Line:
        """Convert the edge geometry to a line.

        Returns
        -------
        Line
            A COMPAS line.

        Raises
        ------
        ValueError
            If the underlying geometry is not a line.

        """
        a = self.first_vertex.point
        b = self.last_vertex.point
        return Line(a, b)

    def to_circle(self) -> Circle:
        """Convert the edge geometry to a circle.

        Returns
        -------
        Circle
            A COMPAS circle.

        Raises
        ------
        ValueError
            If the underlying geometry is not a circle.

        """
        if not self.is_circle:
            raise ValueError(f"The underlying geometry is not a circle: {self.type}")

        return circle_to_compas(_brep.edge_to_circle(self.occ_edge))

    def to_ellipse(self) -> Ellipse:
        """Convert the edge geometry to an ellipse.

        Returns
        -------
        Ellipse
            A COMPAS ellipse.

        Raises
        ------
        ValueError
            If the underlying geometry is not an ellipse.

        """
        if not self.is_ellipse:
            raise ValueError(f"The underlying geometry is not an ellipse: {self.type}")

        return ellipse_to_compas(_brep.edge_to_ellipse(self.occ_edge))

    def to_hyperbola(self) -> Hyperbola:
        """Convert the edge geometry to a hyperbola.

        Returns
        -------
        Hyperbola
            A COMPAS hyperbola.

        Raises
        ------
        ValueError
            If the underlying geometry is not a hyperbola.

        """
        if not self.is_hyperbola:
            raise ValueError(f"The underlying geometry is not a hyperbola: {self.type}")

        return hyperbola_to_compas(_brep.edge_to_hyperbola(self.occ_edge))

    def to_parabola(self) -> Parabola:
        """Convert the edge geometry to a parabola.

        Returns
        -------
        Parabola
            A COMPAS parabola.

        Raises
        ------
        ValueError
            If the underlying geometry is not a parabola.

        """
        if not self.is_parabola:
            raise ValueError(f"The underlying geometry is not a parabola: {self.type}")

        return parabola_to_compas(_brep.edge_to_parabola(self.occ_edge))

    def to_bezier(self) -> Bezier:
        """Convert the edge geometry to a bezier curve.

        Returns
        -------
        Bezier
            A COMPAS bezier curve.

        Raises
        ------
        ValueError
            If the underlying geometry is not a bezier curve.

        """
        if not self.is_bezier:
            raise ValueError(f"The underlying geometry is not a bezier: {self.type}")

        return bezier_to_compas(_brep.edge_to_bezier(self.occ_edge))

    def to_bspline(self) -> NurbsCurve:
        """Convert the edge geometry to a bspline.

        Returns
        -------
        NursbCurve
            A COMPAS bspline curve.

        Raises
        ------
        ValueError
            If the underlying geometry is not a bspline.

        """
        if not self.is_bspline:
            raise ValueError(f"The underlying geometry is not a bspline: {self.type}")

        return bspline_to_compas(_brep.edge_to_bspline(self.occ_edge))
