# compas_occt

Fast [OpenCASCADE (OCCT 8)](https://github.com/Open-Cascade-SAS/OCCT) geometry for COMPAS —
NURBS curves and surfaces, Breps, booleans, and STEP/IGES/STL/BREP I/O.

It's a drop-in replacement for [`compas_occ`](https://github.com/compas-dev/compas_occ) with the
same API, but links OCCT directly through one compiled [nanobind](https://github.com/wjakob/nanobind)
module instead of depending on `pythonocc-core`.

## Install

```bash
pip install compas_occt
```

## Usage

```python
from compas.geometry import Box, Point
from compas.geometry import Brep, NurbsCurve

# COMPAS dispatches to the OCCT backend
brep = Brep.from_box(Box(1))
brep.to_step("box.step")

curve = NurbsCurve.from_points([Point(0, 0, 0), Point(3, 6, 0), Point(6, -3, 3), Point(10, 0, 0)])
print(curve.length())
```

## Documentation

<https://petrasvestartas.github.io/compas_occt/>

## Contributing

See the docs for building from source. Report bugs on the
[issue tracker](https://github.com/petrasvestartas/compas_occt/issues).

## License

MIT
