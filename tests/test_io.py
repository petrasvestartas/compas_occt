import pytest

from compas.geometry import Box
from compas.geometry import Sphere
from compas.tolerance import TOL
from compas_occt.brep import OCCBrep


@pytest.mark.parametrize("fmt", ["step", "iges"])
def test_io_roundtrip_geometry(tmp_path, fmt):
    brep = OCCBrep.from_box(Box(2))
    path = tmp_path / ("shape." + fmt)

    getattr(brep, "to_" + fmt)(path)
    other = getattr(OCCBrep, "from_" + fmt)(path, solid=True)

    assert len(other.faces) == 6
    assert TOL.is_close(other.volume, brep.volume)


def test_step_writes_solid_brep(tmp_path):
    path = tmp_path / "solid.step"
    OCCBrep.from_box(Box(2)).to_step(path)
    text = path.read_text()
    assert text.count("ADVANCED_FACE") == 6
    assert "MANIFOLD_SOLID_BREP" in text


def test_step_with_attributes_roundtrip(tmp_path):
    path = tmp_path / "attrs.step"
    brep = OCCBrep.from_box(Box(2))
    brep.to_step_with_attributes(
        path,
        name="MyBox",
        attributes={"material": "steel", "count": 3, "thickness": 1.5},
    )

    # the metadata is embedded as general_property entities in the STEP file itself
    text = path.read_text()
    assert "GENERAL_PROPERTY" in text
    assert "MyBox" in text

    records = OCCBrep.from_step_with_attributes(path)
    assert len(records) == 1
    shape, name, attributes = records[0]
    assert name == "MyBox"
    assert attributes["material"] == "steel"
    assert attributes["count"] == 3
    assert TOL.is_close(attributes["thickness"], 1.5)
    assert TOL.is_close(shape.volume, brep.volume)


def test_stl_write(tmp_path):
    path = tmp_path / "shape.stl"
    OCCBrep.from_sphere(Sphere(1)).to_stl(path)
    assert path.exists() and path.stat().st_size > 0


def test_brep_write(tmp_path):
    path = tmp_path / "shape.brep"
    OCCBrep.from_box(Box(1)).to_brep(path)
    assert path.exists() and path.stat().st_size > 0
