# compas_occt

Direct, lean [nanobind](https://github.com/wjakob/nanobind) bindings to the
[OpenCASCADE Technology (OCCT) 8](https://github.com/Open-Cascade-SAS/OCCT) geometry kernel,
packaged as a drop-in replacement for [`compas_occ`](https://github.com/compas-dev/compas_occ).

`compas_occt` exposes the exact same public API as `compas_occ` — NURBS curves and surfaces
(`OCCNurbsCurve`, `OCCNurbsSurface`), Boundary Representations (`OCCBrep` and its
vertex/edge/loop/face components), booleans, fillet/offset/slice, STEP/IGES/STL/BREP I/O, and
the COMPAS plugin factories so `compas.geometry.Brep.from_box(...)` returns an `OCCBrep`. The
difference is the backend: instead of `pythonocc-core`, it links OCCT directly through a single
compiled extension module, with no `pythonocc-core` dependency.

## Design

- **One extension module.** All OCCT-backed functions live in a single `compas_occt._occt`
  module that links OCCT exactly once. This keeps RTTI/memory consistent across the whole API
  (required for STEP/IGES) and is far leaner than one OCCT copy per submodule.
- **Functional backend + opaque handles.** Thin C++ free functions operate on four opaque
  handle wrappers (`Shape`, `GeomCurve`, `Geom2dCurve`, `GeomSurface`); the Python classes hold
  one of these in `self._native` and delegate.
- **Zero-copy data transfer.** Bulk coordinate data (mesh tessellation, NURBS control points,
  curve discretisation) crosses the C++↔Python boundary as `numpy` arrays that view the C++
  buffer directly (no copy). numpy — not jax — is the right tool here: it is the zero-copy
  buffer-protocol partner for nanobind's `ndarray`, lightweight, and already a dependency.

## Installation

```bash
pip install compas_occt
```

Development install (builds OCCT 8 from source on first build; cached afterwards):

```bash
git clone https://github.com/petrasvestartas/compas_occt.git
cd compas_occt
pip install --no-build-isolation -ve ".[dev]"
```

A C++17 compiler, CMake ≥ 3.15 and Ninja are required for the source build. On Windows, run the
command from a Visual Studio "x64 Native Tools" prompt (or after calling `vcvars64.bat`).

### Development with [uv](https://github.com/astral-sh/uv)

`uv` gives a fast, reproducible environment. The first build downloads and compiles OCCT 8
(~30–60 min); it is then cached in `external/occt`, so later builds take a few minutes.

```bash
# 1. create the environment (Python >= 3.9; 3.14 is used here)
uv venv --python 3.14

# 2. install the build backend + the runtime and dev/docs dependencies
uv pip install scikit-build-core nanobind cmake ninja
uv pip install -e ".[dev,docs]" --no-build-isolation

# 3. (only to run the viewer examples) install compas_viewer and patch it for Python 3.14
uv pip install compas_viewer
python tools/patch_compas_viewer.py

# 4. run the tests, examples, or docs
uv run pytest tests/ -v
uv run mkdocs serve
uv run python docs/examples/breps/brep_booleans.py
```

On Windows, run the commands from a Visual Studio "x64 Native Tools" prompt (or after calling
`vcvars64.bat`) so the MSVC toolchain and the `.venv` are both on `PATH`.

> **Python 3.14 note.** `compas_viewer` 2.0.2 crashes on Python 3.14 (it reads
> `self.__annotations__` in a dataclass, which PEP 749 no longer resolves to the class).
> `tools/patch_compas_viewer.py` applies the one-line upstream fix; it is idempotent and only
> needed to run the visualisation examples (the core `compas_occt` API does not need it).

## Usage

```python
from compas.geometry import Box, Point
from compas.geometry import Brep, NurbsCurve

# COMPAS plugin dispatch -> OCC implementation
brep = Brep.from_box(Box(1))
brep.to_step("box.step")

curve = NurbsCurve.from_points([Point(0, 0, 0), Point(3, 6, 0), Point(6, -3, 3), Point(10, 0, 0)])
print(curve.length())
```

## Tests

```bash
pip install --no-build-isolation -ve ".[dev]"
python -m pytest tests/ -v
```

## Documentation

Built with mkdocs (`pip install -e ".[docs]"`, then `mkdocs serve`). Mirrors the `compas_occ`
tutorial, examples, and API reference.

## Issue Tracker

Please report bugs on the [issue tracker](https://github.com/petrasvestartas/compas_occt/issues).
