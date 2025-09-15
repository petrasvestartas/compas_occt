from compas.geometry import Point
from compas_occt._geometry import gp_Pnt_init

# =============================================================================
# To OCC
# =============================================================================


def gp_Pnt(point: Point):
    """Convert a COMPAS point to an OCC point using zero-copy unique_ptr.

    Parameters
    ----------
    point : :class:`~compas.geometry.Point`
        The COMPAS point to convert.

    Returns
    -------
    ``unique_ptr<gp_Pnt>``
        Zero-copy unique pointer to OCC point.

    Examples
    --------
    >>> from compas.geometry import Point
    >>> from compas_occt.conversions import gp_Pnt
    >>> point = Point(0, 0, 0)
    >>> gp_Pnt(point)
    <class 'gp_Pnt'>

    """
    return gp_Pnt_init(point.x, point.y, point.z)


# =============================================================================
# TODO: Additional gp_Pnt methods to implement
# =============================================================================

# Basic coordinate operations (already implemented):
# - SetCoord(index, value)
# - SetCoord(x, y, z) 
# - SetX, SetY, SetZ
# - Coord(index), Coord() -> array
# - X(), Y(), Z()
# - Distance, SquareDistance
# - IsEqual

# Barycentric operations:
# - BaryCenter(alpha, point, beta)

# TODO: Transformation methods (require gp_Vec, gp_Ax1, gp_Ax2, gp_Trsf):
# - Mirror(point)
# - Mirror(axis) 
# - Mirror(plane)
# - Mirrored(point)
# - Mirrored(axis)
# - Mirrored(plane)
# - Rotate(axis, angle)
# - Rotated(axis, angle)
# - Scale(center, factor)
# - Scaled(center, factor)
# - Transform(transformation)
# - Transformed(transformation)
# - Translate(vector)
# - Translate(point1, point2)
# - Translated(vector)
# - Translated(point1, point2)

# TODO: Utility methods:
# - DumpJson(stream, depth)
# - InitFromJson(stream, position)