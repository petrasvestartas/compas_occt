"""Transformation conversions between COMPAS and the OCC backend."""

import compas.geometry


def compas_transformation_to_trsf(matrix: compas.geometry.Transformation) -> list[float]:
    """Convert a COMPAS transformation to OCC transformation data.

    The OCC backend builds a ``gp_Trsf`` from the row-major list of the first 12 values
    of the 4x4 matrix (``SetValues``). ``gp_Trsf`` itself never crosses into Python, so
    this returns that 12-float list, which the C++ transform functions accept directly.

    Parameters
    ----------
    matrix
        A COMPAS transformation.

    Returns
    -------
    list[float]
        The row-major list of the first 12 matrix values.

    """
    return list(matrix.list[:12])
