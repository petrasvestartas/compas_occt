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


def test_boolean_difference_of_a_fragmenting_cut_keeps_the_pieces_as_solids():
    """A cut that splits its target must hand back the pieces as solids.

    OCCT returns a fragmenting boolean as a COMPOUND holding one solid per
    connected piece. Sewing or healing that compound flattens it into loose
    shells, which makes the pieces unreachable: ``.solids`` reports nothing, so
    there is no way to select the real body out of a carved part plus its
    slivers, and ``.volume`` silently sums every fragment instead of measuring
    one part.
    """
    cube = OCCBrep.from_box(Box(10))  # z from -5 to 5
    knife = OCCBrep.from_box(Box(20, 20, 1))  # spans x/y completely, z from -0.5 to 0.5

    diff = cube - knife

    assert len(diff.solids) == 2, "the two halves must survive as separate solids"
    for piece in diff.solids:
        assert piece.is_solid
        assert TOL.is_close(piece.volume, 10 * 10 * 4.5)
    assert TOL.is_close(sum(piece.volume for piece in diff.solids), 1000.0 - 100.0)


def test_boolean_difference_of_a_single_piece_result_is_a_solid():
    """A cut that leaves one piece must report itself as that solid.

    The kernel still wraps it in a compound; returning the compound would leave
    ``is_solid`` False and make callers unwrap a shape that has nothing to
    unwrap.
    """
    diff = OCCBrep.from_box(Box(10)) - OCCBrep.from_box(Box(20, 2, 2))

    assert diff.is_solid
    assert len(diff.solids) == 1
    assert TOL.is_close(diff.volume, 1000.0 - 10 * 2 * 2)


def test_boolean_union_of_touching_boxes_is_a_solid():
    box = Box(2)
    box.translate([2, 0, 0])  # face-to-face with the first at x = 1

    union = OCCBrep.from_box(Box(2)) + OCCBrep.from_box(box)

    assert union.is_solid
    assert len(union.solids) == 1
    assert TOL.is_close(union.volume, 16.0)
