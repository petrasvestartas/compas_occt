"""
Point geometry with STEP export capabilities.
"""

from compas_occt import _point

__all__ = ["Point"]


class Point:
    """A 3D point with STEP export capabilities.

    Parameters
    ----------
    x : float
        X coordinate.
    y : float
        Y coordinate.
    z : float
        Z coordinate.

    Examples
    --------
    >>> from compas_occt.point import Point
    >>> pt = Point(1.0, 2.0, 3.0)
    >>> pt.to_step("point.step", name="MyPoint", color=[0.0, 1.0, 0.0], attributes={"material": "steel", "weight": "0.1kg"})
    """

    def __init__(self, x, y, z):
        self._point = _point.Point(float(x), float(y), float(z))

    @property
    def x(self):
        """float: X coordinate."""
        return self._point.x

    @property
    def y(self):
        """float: Y coordinate."""
        return self._point.y

    @property
    def z(self):
        """float: Z coordinate."""
        return self._point.z

    def to_step(self, filepath, name="Point", color=None, attributes=None):
        """Export point to STEP file.

        Parameters
        ----------
        filepath : str or Path
            Path to the STEP file.
        name : str, optional
            Name of the point in the STEP file. Default is "Point".
        color : list of float, optional
            RGB color values [r, g, b] in range [0, 1]. Default is red [1, 0, 0].
        attributes : dict, optional
            Dictionary of custom attributes to attach to the point.

        Returns
        -------
        bool
            True if export was successful, False otherwise.

        Examples
        --------
        >>> pt = Point(0, 0, 0)
        >>> pt.to_step("origin.step", name="Origin", color=[0, 0, 1], attributes={"type": "reference_point"})
        """
        if color is None:
            color = [1.0, 0.0, 0.0]  # Default red
        if attributes is None:
            attributes = {}

        return self._point.to_step(str(filepath), name, color, attributes)

    def __repr__(self):
        return f"Point({self.x}, {self.y}, {self.z})"
