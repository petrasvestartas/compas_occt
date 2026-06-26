from compas.geometry import Box
from compas.tolerance import TOL
from compas_occt.brep import OCCBrep


def test_boolean_union():
    a = OCCBrep.from_box(Box(2))
    b = OCCBrep.from_box(Box(2))
    union = a + b
    assert isinstance(union, OCCBrep)
    assert TOL.is_close(union.volume, 8.0)  # fully overlapping boxes


def test_boolean_difference():
    a = OCCBrep.from_box(Box(2))
    b = OCCBrep.from_box(Box(1))
    diff = a - b
    assert isinstance(diff, OCCBrep)
    assert TOL.is_close(diff.volume, 8.0 - 1.0)


def test_boolean_intersection():
    a = OCCBrep.from_box(Box(2))
    b = OCCBrep.from_box(Box(1))
    common = a & b
    assert isinstance(common, OCCBrep)
    assert TOL.is_close(common.volume, 1.0)


def test_overlap_intersection():
    a = OCCBrep.from_box(Box(1))
    box = Box(1)
    box.translate([1, 0.3, 0.5])  # B sits face-to-face with A at x = 0.5
    b = OCCBrep.from_box(box)

    common = a.overlap_intersection(b)
    assert isinstance(common, OCCBrep)
    assert len(common.faces) == 1
    assert TOL.is_close(common.area, 0.7 * 0.5)  # the shared rectangle on the x = 0.5 plane
