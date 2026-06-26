from compas.geometry import BrepLoop
from compas.geometry import Polygon
from compas.geometry import Polyline
from compas.itertools import pairwise
from compas_occt import _occt as _brep
from compas_occt.brep import OCCBrepEdge
from compas_occt.brep import OCCBrepVertex


def wire_from_edges(edges: list[OCCBrepEdge]):
    """Construct a wire from a list of edges.

    Parameters
    ----------
    edges
        The edges.

    Returns
    -------
    Shape

    """
    return _brep.make_wire([edge.occ_edge for edge in edges])


class OCCBrepLoop(BrepLoop):
    """Class representing an edge loop in the BRep of a geometric shape.

    Parameters
    ----------
    occ_wire
        An OCC BRep wire.

    Attributes
    ----------
    vertices
        List of BRep vertices.
    edges
        List of BRep edges.

    """

    @property
    def __data__(self) -> dict:
        raise NotImplementedError

    @classmethod
    def __from_data__(cls, data: dict) -> "OCCBrepLoop":
        raise NotImplementedError

    def __init__(self, occ_wire):
        super().__init__()
        self._occ_wire = occ_wire

    def __eq__(self, other: "OCCBrepLoop") -> bool:
        return self.is_equal(other)

    def is_same(self, other: "OCCBrepLoop") -> bool:
        """Check if this loop is the same as another loop.

        Two loops are the same if they have the same location.

        Parameters
        ----------
        other
            The other loop.

        Returns
        -------
        bool
            ``True`` if the loops are the same, ``False`` otherwise.

        """
        if not isinstance(other, OCCBrepLoop):
            return False
        return _brep.shape_is_same(self.occ_wire, other.occ_wire)

    def is_equal(self, other: "OCCBrepLoop") -> bool:
        """Check if this loop is equal to another loop.

        Two loops are equal if they have the same location and orientation.

        Parameters
        ----------
        other
            The other loop.

        Returns
        -------
        bool
            ``True`` if the loops are equal, ``False`` otherwise.

        """
        if not isinstance(other, OCCBrepLoop):
            return False
        return _brep.shape_is_equal(self.occ_wire, other.occ_wire)

    # ==============================================================================
    # OCC Properties
    # ==============================================================================

    @property
    def occ_shape(self):
        return self._occ_wire

    @property
    def occ_wire(self):
        return self._occ_wire

    @occ_wire.setter
    def occ_wire(self, loop) -> None:
        self._occ_wire = loop

    # ==============================================================================
    # Properties
    # ==============================================================================

    @property
    def is_valid(self) -> bool:
        return _brep.is_valid(self.occ_wire)

    @property
    def vertices(self) -> list[OCCBrepVertex]:
        return [OCCBrepVertex(vertex) for vertex in _brep.wire_explore_vertices(self.occ_wire)]

    @property
    def edges(self) -> list[OCCBrepEdge]:
        return [OCCBrepEdge(edge) for edge in _brep.wire_explore_edges(self.occ_wire)]

    @edges.setter
    def edges(self, edges: list[OCCBrepEdge]) -> None:
        self.occ_wire = wire_from_edges(edges)

    # ==============================================================================
    # Constructors
    # ==============================================================================

    @classmethod
    def from_edges(cls, edges: list[OCCBrepEdge]) -> "OCCBrepLoop":
        """Construct a loop from a collection of edges.

        Parameters
        ----------
        edges
            The edges.

        Returns
        -------
        OCCBrepLoop

        """
        return cls(wire_from_edges(edges))

    @classmethod
    def from_polyline(cls, polyline: Polyline) -> "OCCBrepLoop":
        """Construct a loop from a polyline.

        Parameters
        ----------
        polyline
            The polyline.

        Returns
        -------
        OCCBrepLoop

        """
        edges = []
        for a, b in pairwise(polyline.points):
            edge = OCCBrepEdge.from_point_point(a, b)
            edges.append(edge)
        return cls(wire_from_edges(edges))

    @classmethod
    def from_polygon(cls, polygon: Polygon) -> "OCCBrepLoop":
        """Construct a loop from a polygon.

        Parameters
        ----------
        polygon
            The polygon.

        Returns
        -------
        OCCBrepLoop

        """
        edges = []
        for a, b in pairwise(polygon.points + polygon.points[:1]):
            edge = OCCBrepEdge.from_point_point(a, b)
            edges.append(edge)
        return cls(wire_from_edges(edges))

    # ==============================================================================
    # Conversions
    # ==============================================================================

    def to_polyline(self) -> Polyline:
        """Convert the loop to a polyline.

        Returns
        -------
        Polyline

        """
        points = []
        for vertex in self.vertices:
            points.append(vertex.point)
        return Polyline(points)

    def to_polygon(self) -> Polygon:
        """Convert the loop to a simple polygon without underlying geometry.

        Returns
        -------
        Polygon

        """
        points = []
        for vertex in self.vertices:
            points.append(vertex.point)
        return Polygon(points)

    # ==============================================================================
    # Methods
    # ==============================================================================

    def fix(self) -> None:
        """Try to fix the loop.

        Returns
        -------
        None

        """
        self.occ_wire = _brep.fix_wire(self.occ_wire)
