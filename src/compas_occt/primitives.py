from compas_occt import _primitives  # The actual C++ module


def add(a, b):
    """Add two numbers together."""
    return _primitives.add(a, b)
