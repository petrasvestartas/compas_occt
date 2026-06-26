from compas.geometry import BrepVertex
from compas.geometry import Point
from compas_occt import _occt as _brep
from compas_occt.conversions import point_to_compas
from compas_occt.conversions.geometry import point_to_occ


class OCCBrepVertex(BrepVertex):
    """Class representing a vertex in the BRep of a geometric shape.

    Parameters
    ----------
    occ_vertex
        An OCC topological vertex data structure.

    Attributes
    ----------
    point : Point
        The geometric point underlying the topological vertex.

    """

    @property
    def __data__(self) -> dict:
        return {"point": self.point}

    @classmethod
    def __from_data__(cls, data: dict) -> "OCCBrepVertex":
        raise NotImplementedError

    def __init__(self, occ_vertex):
        super().__init__()
        self._occ_vertex = occ_vertex

    def __eq__(self, other: "OCCBrepVertex") -> bool:
        return self.is_equal(other)

    def is_same(self, other: "OCCBrepVertex") -> bool:
        """Check if this vertex is the same as another vertex.

        Two vertices are the same if they have the same location.

        Parameters
        ----------
        other
            The other vertex.

        Returns
        -------
        bool
            ``True`` if the vertices are the same, ``False`` otherwise.

        """
        if not isinstance(other, OCCBrepVertex):
            return False
        return _brep.shape_is_same(self.occ_vertex, other.occ_vertex)

    def is_equal(self, other: "OCCBrepVertex") -> bool:
        """Check if this vertex is equal to another vertex.

        Two vertices are equal if they have the same location and orientation.

        Parameters
        ----------
        other
            The other vertex.

        Returns
        -------
        bool
            ``True`` if the vertices are equal, ``False`` otherwise.

        """
        if not isinstance(other, OCCBrepVertex):
            return False
        return _brep.shape_is_equal(self.occ_vertex, other.occ_vertex)

    # ==============================================================================
    # OCC Properties
    # ==============================================================================

    @property
    def occ_vertex(self):
        return self._occ_vertex

    @occ_vertex.setter
    def occ_vertex(self, occ_vertex) -> None:
        self._occ_vertex = occ_vertex

    # ==============================================================================
    # Properties
    # ==============================================================================

    @property
    def point(self) -> Point:
        return point_to_compas(_brep.vertex_point(self.occ_vertex))

    @point.setter
    def point(self, point: Point) -> None:
        self._occ_vertex = _brep.make_vertex(point_to_occ(point))

    # ==============================================================================
    # Constructors
    # ==============================================================================

    @classmethod
    def from_point(cls, point: Point) -> "BrepVertex":
        """Construct a vertex from a point.

        Parameters
        ----------
        point
            The point.

        Returns
        -------
        BrepVertex
            The vertex.

        """
        return cls(_brep.make_vertex(point_to_occ(point)))

    # ==============================================================================
    # Conversions
    # ==============================================================================

    def to_point(self) -> Point:
        """Convert the vertex to a point.

        Returns
        -------
        Point
            The point.

        """
        return self.point
