# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

### Changed

### Removed

## [0.1.16] 2026-06-27

### Added

- Full `compas_occ` public API: `OCCCurve`, `OCCCurve2d`, `OCCNurbsCurve`, `OCCSurface`, `OCCNurbsSurface`, `OCCBrep` (+ vertex/edge/loop/face/builder), `conversions`, and the COMPAS plugin factories.
- Direct nanobind bindings to OCCT 8.0.0_p1 in a single `compas_occt._occt` module (one OCCT copy).
- STEP / IGES / STL / BREP read & write.
- `OCCBrep.to_step_with_attributes` / `from_step_with_attributes`: STEP read & write with a per-shape name and user-defined string/integer/real attributes, stored as `general_property` entities via the OCCT XDE layer (cf. OCCT PR #634).
- `OCCBrep.overlap_intersection`: the common (shared) region of the faces where two Breps overlap (the boolean intersection of the overlapping faces found by `overlap`).
- Zero-copy `numpy` transfer for tessellation, NURBS control points, and curve discretisation.
- Tests for I/O round-trips (incl. STEP attributes), booleans, and zero-copy transfer.
- Example pages: Brep Booleans (union/difference/intersection), Merge Coplanar Faces, and STEP File With Attributes, each with a generated screenshot.
- Tutorial sections for curves, surfaces, breps, and visualisation.

### Fixed

- Pass `STABLE_ABI` to `nanobind_add_module` so the compiled `_occt` extension actually targets Python's stable ABI, matching `wheel.py-api = "cp312"`. Previously the wheel was tagged `cp312-abi3` but contained a version-specific module, so cibuildwheel's cp313/cp314 test stage failed with `ImportError: cannot import name '_occt' from 'compas_occt'`.
- Pin `typing-extensions>=4.14.1` in the cibuildwheel test environment to silence the `pydantic` dependency-conflict warning.

### Changed

- Consolidated the per-domain extension modules into a single `_occt` module so OCCT RTTI/memory is shared across the whole API (this is what makes STEP/IGES round-trip geometry).
- CMake builds OCCT 8.0.0_p1 with DataExchange enabled and FreeType disabled; links the Win32 system libraries plus `TKV3d`/`TKService` (required by the XDE `XCAFDoc_VisMaterial` path). OCCT is cached under `external/occt` (like Eigen).
- Performance: curve `point_at`/`tangent_at`/`curvature_at`/`frame_at` do the domain bounds-check in C++ (one boundary crossing instead of two, ~16% faster); bulk point-list conversions (`points`, `to_points`, `to_polyline`, control points) build COMPAS points from a single `numpy.tolist()` (~25-30% faster).

### Removed

- Dependency on `pythonocc-core`.
- Obsolete proof-of-concept demo modules and the Sphinx docs skeleton (replaced by an mkdocs site mirroring `compas_occ`).


## [0.1.15] 2025-05-21

### Added

### Changed

### Removed


## [0.1.14] 2025-05-19

### Added

### Changed

- CMakeLists.txt is fixed to build OCCT static libraries.

### Removed


## [0.1.13] 2025-05-19

### Added

### Changed

- WIP

### Removed


## [0.1.12] 2025-05-19

### Added

### Changed

- WIP

### Removed


## [0.1.12] 2025-05-19

### Added

### Changed

- WIP

### Removed

## [0.1.11] 2025-05-19

### Added

### Changed

- WIP

### Removed

## [0.1.10] 2025-05-18

### Added

### Changed

- WIP

### Removed


## [0.1.9] 2025-05-18

### Added

### Changed

- WIP

### Removed


## [0.1.8] 2025-05-18

### Added

### Changed

- WIP

### Removed


## [0.1.7] 2025-05-18

### Added

### Changed

- WIP

### Removed


## [0.1.6] 2025-05-18

### Added

### Changed

- WIP Universal Binary Support for macOS.

### Removed


## [0.1.5] 2025-05-18

### Added

- Universal Binary Support for macOS.
- OCCT Configuration Fixed
- OCCT Configuration Fixed

### Changed

### Removed

## [0.1.7] 2025-05-18

### Added

### Changed

- Ninja generator for windows, disables modules, add clear build status messages.

### Removed

## [0.1.6] 2025-05-18

### Added

### Changed

- WIP

### Removed

## [0.1.5] 2025-05-18

### Added

### Changed

- WIP

### Removed


## [0.1.4] 2025-05-18

### Added

### Changed

- Revert back github release action to build 3 OS jobs.

### Removed


## [0.1.3] 2025-05-18

### Added

### Changed

- Fix release github action to build 12 jobs.

### Removed

- Remove unnecessary bash commands in pyproject.toml.


## [0.1.2] 2025-05-18

### Added

### Changed

- Split release into multiple python versions.

### Removed


## [0.1.1] 2025-05-16

### Added

- CMakeLists.txt for building OCCT extensions.

### Changed

### Removed


## [0.1.0] 2025-05-15

### Added

- Initial release for CI testing purposes.

### Changed

### Removed

