import pytest
import random

from compas.geometry import Box
from compas.geometry import Cylinder
from compas.geometry import Frame
from compas.geometry import Sphere
from compas.tolerance import TOL
from compas_occt.brep import OCCBrep


@pytest.mark.parametrize(
    "box",
    [
        Box(1),
        Box(1, 2, 3),
        Box(random.random()),
        Box(random.random(), random.random(), random.random()),
        Box(1, frame=Frame(point=[random.random(), random.random(), random.random()])),
        Box(1, 2, 3, frame=Frame(point=[random.random(), random.random(), random.random()])),
        Box(random.random(), frame=Frame(point=[random.random(), random.random(), random.random()])),
        Box(random.random(), random.random(), random.random(), frame=Frame(point=[random.random(), random.random(), random.random()])),
    ],
)
def test_brep_from_box(box: Box):
    brep = OCCBrep.from_box(box)
    brep.heal()

    assert TOL.is_close(box.volume, brep.volume)
    assert len(box.points) == len(brep.points)
    assert box.frame.point == brep.centroid
    # assert all(a == b for a, b in zip(box.points, box.points))


def test_brep_from_cylinder():
    cylinder = Cylinder(radius=1, height=1)
    brep = OCCBrep.from_cylinder(cylinder)

    assert TOL.is_close(cylinder.volume, brep.volume)
    assert cylinder.frame.point == brep.centroid


def test_brep_from_sphere():
    sphere = Sphere(1)
    brep = OCCBrep.from_sphere(sphere)

    assert TOL.is_close(sphere.volume, brep.volume)
    assert sphere.frame.point == brep.centroid


def test_brep_caches_invalidated_on_transform():
    """In-place transform must invalidate the cached topology and properties."""
    from compas.geometry import Translation

    brep = OCCBrep.from_box(Box(1))
    # populate the caches
    v_before = brep.faces[0].vertices[0].point
    c_before = brep.centroid

    brep.transform(Translation.from_vector([10, 0, 0]))

    # cached topology + centroid must reflect the moved geometry, not the stale one
    assert TOL.is_close(brep.faces[0].vertices[0].point.x, v_before.x + 10)
    assert TOL.is_close(brep.centroid.x, c_before.x + 10)
    # rigid transform preserves volume
    assert TOL.is_close(brep.volume, 1.0)
