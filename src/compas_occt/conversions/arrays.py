"""Array conversions between COMPAS data and OCC-style arrays.

In ``compas_occ`` these helpers build real ``TColgp_*``/``TColStd_*`` OCC arrays and hand
them to pythonocc constructors. ``compas_occt`` has a *functional* C++ backend whose
constructors take plain Python lists, so OCC arrays never need to cross the boundary.

These functions therefore return lightweight **pure-Python shim objects** that reproduce
exactly the 1-based ``TCol*`` interface used by the test-suite and any introspecting code
(``Length()``, iteration yielding items with ``X()/Y()/Z()``, ``Value()/SetValue()``,
``LowerRow()/UpperCol()/NbRows()`` ...). No compiled extension is required for this module.
"""

from typing import Sequence

from compas.geometry import Point


class _Pnt:
    """Minimal stand-in for an OCC ``gp_Pnt`` exposing the ``X()/Y()/Z()`` accessors."""

    __slots__ = ("_x", "_y", "_z")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self._x = float(x)
        self._y = float(y)
        self._z = float(z)

    def X(self) -> float:  # noqa: N802
        return self._x

    def Y(self) -> float:  # noqa: N802
        return self._y

    def Z(self) -> float:  # noqa: N802
        return self._z

    def SetX(self, value: float) -> None:  # noqa: N802
        self._x = float(value)

    def SetY(self, value: float) -> None:  # noqa: N802
        self._y = float(value)

    def SetZ(self, value: float) -> None:  # noqa: N802
        self._z = float(value)

    def Coord(self) -> tuple[float, float, float]:  # noqa: N802
        return (self._x, self._y, self._z)

    def __iter__(self):
        yield self._x
        yield self._y
        yield self._z

    def __repr__(self) -> str:
        return "gp_Pnt({}, {}, {})".format(self._x, self._y, self._z)


class _Array1:
    """Pure-Python stand-in for a 1-based, one-dimensional OCC ``TCol*_Array1``."""

    __slots__ = ("_lower", "_items")

    def __init__(self, lower: int, upper: int, default=None):
        self._lower = lower
        self._items = [default for _ in range(upper - lower + 1)]

    def Lower(self) -> int:  # noqa: N802
        return self._lower

    def Upper(self) -> int:  # noqa: N802
        return self._lower + len(self._items) - 1

    def Length(self) -> int:  # noqa: N802
        return len(self._items)

    def Size(self) -> int:  # noqa: N802
        return len(self._items)

    def Value(self, index: int):  # noqa: N802
        return self._items[index - self._lower]

    def SetValue(self, index: int, value) -> None:  # noqa: N802
        self._items[index - self._lower] = value

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)


class _Array2:
    """Pure-Python stand-in for a 1-based, two-dimensional OCC ``TCol*_Array2``."""

    __slots__ = ("_lr", "_lc", "_nr", "_nc", "_items")

    def __init__(self, lower_row: int, upper_row: int, lower_col: int, upper_col: int, default=None):
        self._lr = lower_row
        self._lc = lower_col
        self._nr = upper_row - lower_row + 1
        self._nc = upper_col - lower_col + 1
        self._items = [[default for _ in range(self._nc)] for _ in range(self._nr)]

    def LowerRow(self) -> int:  # noqa: N802
        return self._lr

    def UpperRow(self) -> int:  # noqa: N802
        return self._lr + self._nr - 1

    def LowerCol(self) -> int:  # noqa: N802
        return self._lc

    def UpperCol(self) -> int:  # noqa: N802
        return self._lc + self._nc - 1

    def NbRows(self) -> int:  # noqa: N802
        return self._nr

    def NbColumns(self) -> int:  # noqa: N802
        return self._nc

    def Value(self, i: int, j: int):  # noqa: N802
        return self._items[i - self._lr][j - self._lc]

    def SetValue(self, i: int, j: int, value) -> None:  # noqa: N802
        self._items[i - self._lr][j - self._lc] = value


# =============================================================================
# Points
# =============================================================================


def array1_from_points1(points: list[Point]) -> _Array1:
    """Construct a one-dimensional point array from a list of points.

    See Also
    --------
    * [`harray1_from_points1`][harray1_from_points1]
    * [`points1_from_array1`][points1_from_array1]

    """
    points = list(points)
    array = _Array1(1, len(points))
    for index, point in enumerate(points):
        array.SetValue(index + 1, _Pnt(*point))
    return array


def harray1_from_points1(points: list[Point]) -> _Array1:
    """Construct a handled one-dimensional point array from a list of points.

    See Also
    --------
    * [`array1_from_points1`][array1_from_points1]

    """
    return array1_from_points1(points)


def points1_from_array1(array: _Array1) -> list[Point]:
    """Construct a list of points from a one-dimensional point array.

    See Also
    --------
    * [`array1_from_points1`][array1_from_points1]

    """
    return [Point(point.X(), point.Y(), point.Z()) for point in array]


def array2_from_points2(points: list[list[Point]]) -> _Array2:
    """Construct a two-dimensional point array from a list of lists of points.

    See Also
    --------
    * [`points2_from_array2`][points2_from_array2]

    """
    points_as_columns = list(zip(*points))
    rows = len(points_as_columns)
    cols = len(points_as_columns[0])
    array = _Array2(1, rows, 1, cols)
    for i, row in enumerate(points_as_columns):
        for j, point in enumerate(row):
            array.SetValue(i + 1, j + 1, _Pnt(*point))
    return array


def points2_from_array2(array: _Array2) -> list[list[Point]]:
    """Construct a list of lists of points from a two-dimensional point array.

    See Also
    --------
    * [`array2_from_points2`][array2_from_points2]

    """
    points = [[None for j in range(array.NbRows())] for i in range(array.NbColumns())]
    for i in range(array.LowerCol(), array.UpperCol() + 1):
        for j in range(array.LowerRow(), array.UpperRow() + 1):
            pnt = array.Value(j, i)
            points[i - 1][j - 1] = Point(pnt.X(), pnt.Y(), pnt.Z())  # type: ignore
    return points  # type: ignore


# =============================================================================
# Numbers
# =============================================================================


def array1_from_integers1(numbers: list[int]) -> _Array1:
    """Construct a one-dimensional integer array from a list of integers.

    See Also
    --------
    * [`array1_from_floats1`][array1_from_floats1]

    """
    numbers = list(numbers)
    array = _Array1(1, len(numbers))
    for index, number in enumerate(numbers):
        array.SetValue(index + 1, int(number))
    return array


def array1_from_floats1(numbers: list[float]) -> _Array1:
    """Construct a one-dimensional float array from a list of floats.

    See Also
    --------
    * [`array1_from_integers1`][array1_from_integers1]
    * [`array2_from_floats2`][array2_from_floats2]

    """
    numbers = list(numbers)
    array = _Array1(1, len(numbers))
    for index, number in enumerate(numbers):
        array.SetValue(index + 1, float(number))
    return array


def array2_from_floats2(numbers: list[list[float]]) -> _Array2:
    """Construct a two-dimensional real array from a list of lists of floats.

    See Also
    --------
    * [`array1_from_floats1`][array1_from_floats1]

    """
    numberlists_as_columns = list(zip(*numbers))
    rows = len(numberlists_as_columns)
    cols = len(numberlists_as_columns[0])
    array = _Array2(1, rows, 1, cols)
    for i, row in enumerate(numberlists_as_columns):
        for j, number in enumerate(row):
            array.SetValue(i + 1, j + 1, float(number))
    return array


def floats2_from_array2(array: _Array2) -> list[Sequence[float]]:
    """Construct a list of lists of floats from a two-dimensional array of real numbers.

    See Also
    --------
    * [`array2_from_floats2`][array2_from_floats2]

    """
    numbers = []
    for i in range(array.LowerRow(), array.UpperRow() + 1):
        row = []
        for j in range(array.LowerCol(), array.UpperCol() + 1):
            number = array.Value(i, j)
            row.append(number)
        numbers.append(row)
    return list(zip(*numbers))
