"""Low-level OCC shape helpers for the brep layer.

Ported from ``compas_occ.occ`` to the functional ``compas_occt`` backend: every helper takes
and returns opaque ``Shape`` handle wrappers and delegates the topology work to the ``_occt``
extension module.
"""

from compas.geometry import Point
from compas_occt import _occt as _brep
from compas_occt.conversions import point_to_compas

# TopAbs_ShapeEnum integer codes (see brep_explore.cpp).
COMPOUND = 0
COMPSOLID = 1
SOLID = 2
SHELL = 3
FACE = 4
WIRE = 5
EDGE = 6
VERTEX = 7


def split_shapes(arguments: list, tools: list) -> list:
    """Split a group of breps by another group of breps.

    Parameters
    ----------
    arguments : list[Shape]
        The arguments passed to the command.
    tools : list[Shape]
        The tools passed to the command.

    Returns
    -------
    list[Shape]
        The resulting breps.

    """
    return _brep.split(list(arguments), list(tools))


def compute_shape_centreofmass(occ_shape) -> Point:
    """Return a COMPAS Point at the centre of mass of a Brep.

    Parameters
    ----------
    occ_shape : Shape
        The brep.

    Returns
    -------
    :class:`Point`
        The centroid.

    """
    return point_to_compas(_brep.centroid(occ_shape))


def occ_shape_find_vertices(occ_shape) -> list:
    """Find all the vertices in an OCC shape.

    Parameters
    ----------
    occ_shape : Shape
        The shape to explore.

    Returns
    -------
    list[Shape]

    """
    return _brep.shape_explore(occ_shape, VERTEX)


def occ_shape_find_edges(occ_shape) -> list:
    """Find all the edges in an OCC shape.

    Parameters
    ----------
    occ_shape : Shape
        The shape to explore.

    Returns
    -------
    list[Shape]

    """
    return _brep.shape_explore(occ_shape, EDGE)


def occ_shape_find_loops(occ_shape) -> list:
    """Find all the loops or wires in an OCC shape.

    Parameters
    ----------
    occ_shape : Shape
        The shape to explore.

    Returns
    -------
    list[Shape]

    """
    return _brep.shape_explore(occ_shape, WIRE)


def occ_shape_find_faces(occ_shape) -> list:
    """Find all the faces in an OCC shape.

    Parameters
    ----------
    occ_shape : Shape
        The shape to explore.

    Returns
    -------
    list[Shape]

    """
    return _brep.shape_explore(occ_shape, FACE)


def occ_shape_find_shells(occ_shape) -> list:
    """Find all the shells in an OCC shape.

    Parameters
    ----------
    occ_shape : Shape
        The shape to explore.

    Returns
    -------
    list[Shape]

    """
    return _brep.shape_explore(occ_shape, SHELL)


def occ_shape_find_solids(occ_shape) -> list:
    """Find all the solids in an OCC shape.

    Parameters
    ----------
    occ_shape : Shape
        The shape to explore.

    Returns
    -------
    list[Shape]

    """
    return _brep.shape_explore(occ_shape, SOLID)
