"""
COMPAS OCCT geometry tests.

Run tests:
    python -m pytest tests/ -v
    python -m pytest tests/geometry_test.py -v
    python -m pytest tests/geometry_test.py::TestGpPnt -v
    python -m pytest tests/geometry_test.py::TestGpPnt::test_creation -v
"""

from compas.geometry import Point
from compas_occt.conversions import gp_Pnt

class TestGpPnt:
    """Test class for gp_Pnt geometry operations."""

    def test_creation(self):
        """Test point creation and coordinate access."""
        point = Point(1.0, 2.0, 3.0)
        occ_point = gp_Pnt(point)
        assert occ_point is not None
        assert occ_point.X() == 1.0
        assert occ_point.Y() == 2.0
        assert occ_point.Z() == 3.0

    def test_setters(self):
        """Test coordinate setters."""
        point = Point(0.0, 0.0, 0.0)
        occ_point = gp_Pnt(point)
        
        occ_point.SetX(5.0)
        occ_point.SetY(6.0)
        occ_point.SetZ(7.0)
        
        assert occ_point.X() == 5.0
        assert occ_point.Y() == 6.0
        assert occ_point.Z() == 7.0

    def test_set_coord(self):
        """Test SetCoord method."""
        point = Point(0.0, 0.0, 0.0)
        occ_point = gp_Pnt(point)
        
        occ_point.SetCoord(10.0, 20.0, 30.0)
        
        assert occ_point.X() == 10.0
        assert occ_point.Y() == 20.0
        assert occ_point.Z() == 30.0

    def test_coord(self):
        """Test Coord method returning array."""
        point = Point(1.5, 2.5, 3.5)
        occ_point = gp_Pnt(point)
        
        coords = occ_point.Coord()
        assert len(coords) == 3
        assert coords[0] == 1.5
        assert coords[1] == 2.5
        assert coords[2] == 3.5

    def test_distance(self):
        """Test Distance method."""
        point1 = Point(0.0, 0.0, 0.0)
        point2 = Point(3.0, 4.0, 0.0)
        
        occ_point1 = gp_Pnt(point1)
        occ_point2 = gp_Pnt(point2)
        
        distance = occ_point1.Distance(occ_point2)
        assert abs(distance - 5.0) < 1e-10  # 3-4-5 triangle

    def test_square_distance(self):
        """Test SquareDistance method."""
        point1 = Point(0.0, 0.0, 0.0)
        point2 = Point(3.0, 4.0, 0.0)
        
        occ_point1 = gp_Pnt(point1)
        occ_point2 = gp_Pnt(point2)
        
        sq_distance = occ_point1.SquareDistance(occ_point2)
        assert abs(sq_distance - 25.0) < 1e-10  # 3² + 4² = 25

    def test_equality(self):
        """Test IsEqual and __eq__ methods."""
        point1 = Point(1.0, 2.0, 3.0)
        point2 = Point(1.0, 2.0, 3.0)
        point3 = Point(1.1, 2.0, 3.0)
        
        occ_point1 = gp_Pnt(point1)
        occ_point2 = gp_Pnt(point2)
        occ_point3 = gp_Pnt(point3)
        
        # Test Python equality operator
        assert occ_point1 == occ_point2
        assert not (occ_point1 == occ_point3)

    def test_repr(self):
        """Test string representation."""
        point = Point(1.5, 2.5, 3.5)
        occ_point = gp_Pnt(point)
        
        repr_str = repr(occ_point)
        assert "gp_Pnt" in repr_str
        assert "1.5" in repr_str
        assert "2.5" in repr_str
        assert "3.5" in repr_str


# Example structure for future geometry classes:
# class TestGpVec:
#     """Test class for gp_Vec geometry operations."""
#     pass
#
# class TestGpDir:
#     """Test class for gp_Dir geometry operations."""
#     pass

