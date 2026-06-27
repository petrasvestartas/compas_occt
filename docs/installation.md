# Installation

## Stable

```bash
pip install compas_occt
```

Several examples use the COMPAS Viewer for visualisation.
To install `compas_viewer` in the same environment

```bash
pip install compas_viewer
```

## Development

Build from a local clone of the repo.

```bash
git clone https://github.com/petrasvestartas/compas_occt.git
cd compas_occt
pip install --no-build-isolation -ve ".[dev]"
```

### Build requirements

A C++17 compiler, CMake ≥ 3.15, and Ninja. On Windows, run the command from a Visual Studio
"x64 Native Tools" prompt (or after calling `vcvars64.bat`).

The first build downloads and compiles OCCT 8 from source (~30–60 min). It is then cached in
`external/occt`, so later builds take only a few minutes.

### With [uv](https://github.com/astral-sh/uv)

```bash
uv venv --python 3.14
uv pip install scikit-build-core nanobind cmake ninja
uv pip install -e ".[dev,docs]" --no-build-isolation

# tests / docs / examples
uv run pytest tests/ -v
uv run mkdocs serve
```

To run the viewer examples on Python 3.14, also `uv pip install compas_viewer` and apply the
one-line upstream fix with `python tools/patch_compas_viewer.py` (idempotent; only needed for the
visualisation examples, not the core API).