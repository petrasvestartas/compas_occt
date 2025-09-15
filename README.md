# compas_occt

Cross-platform (Windows, Mac, Linux) Nanobind wrapper for OCCT, focused on single function calls rather than class wrapping.

![Screenshot 2025-05-23 184722](https://github.com/user-attachments/assets/1cc9662e-5de9-4f58-97f7-13ce489eed1a)

## Tests

```bash
pip install --no-build-isolation .
python -m pytest tests/ -v
```

## Installation

Stable releases can be installed from PyPI.

```bash
pip install compas_occt
```

To install the latest version for development, do:

```bash
git clone https://github.com//compas_occt.git
cd compas_occt
pip install -e ".[dev]"
```

If you are a software developer, and this is your own package, then it is usually much more efficient to install the build dependencies in your environment once and use the following command that avoids a costly creation of a new virtual environment at every compilation:

```bash
pip install --no-build-isolation -ve .
cibuildwheel --output-dir wheelhouse .
```

## Documentation

For further "getting started" instructions, a tutorial, examples, and an API reference,
please check out the online documentation here: [compas_occt docs](https://.github.io/compas_occt)

## Issue Tracker

If you find a bug or if you have a problem with running the code, please file an issue on the [Issue Tracker](https://github.com//compas_occt/issues).

## Migration Plan: Building Your Own OCC Wrapper

This section outlines a step-by-step plan for creating your own OpenCascade wrapper while maintaining the same API as compas_occt.

### Phase 1: Foundation Setup (Start Here)
**Recommended Starting Point: `conversions/` module**

1. **Core Infrastructure**
   - Set up build system (CMakeLists.txt with nanobind)
   - Create basic C++ wrapper structure
   - Implement fundamental type conversions (Point, Vector, Frame)

2. **Start with `conversions/geometry.py`**
   - This is the **BEST STARTING POINT** because:
     - Contains all fundamental geometry conversions
     - Small, focused functions that are easy to test
     - No complex dependencies on other modules
     - Forms the foundation for everything else

3. **Key conversion functions to implement first:**
   ```python
   # From COMPAS to OCC
   point_to_occ()
   vector_to_occ() 
   frame_to_occ_ax3()
   plane_to_occ()
   
   # From OCC to COMPAS
   point_to_compas()
   vector_to_compas()
   ax3_to_compas()
   plane_to_compas()
   ```

### Phase 2: Core Utilities
4. **Implement `occ.py` utilities**
   - Shape exploration functions (find_vertices, find_edges, etc.)
   - Basic shape operations (split_shapes, compute_centroid)
   - These are pure algorithmic functions, easier to port

### Phase 3: Geometry Classes
5. **Basic Geometry (`geometry/curves/` and `geometry/surfaces/`)**
   - Start with `OCCCurve` base class
   - Implement `OCCNurbsCurve` 
   - Then move to `OCCSurface` and `OCCNurbsSurface`
   - Focus on core methods: creation, evaluation, conversion

### Phase 4: BRep Implementation
6. **BRep Foundation (`brep/` module)**
   - Start with `brepvertex.py`, `brepedge.py` (simplest components)
   - Then `brepface.py`, `breploop.py`
   - Finally `brep.py` (most complex, has all boolean operations)

### Phase 5: Advanced Features
7. **Plugin System Integration**
   - Implement COMPAS plugin decorators
   - Register factory methods
   - Ensure API compatibility

8. **I/O and Advanced Operations**
   - STEP/IGES import/export
   - Boolean operations
   - Meshing and tessellation

### Implementation Strategy

#### Build System Approach
- Use **nanobind** instead of pybind11 (as shown in memories)
- Create modular C++ backend with functional approach
- Each Python module maps to focused C++ functions

#### Key Architectural Decisions
1. **Functional vs Object-Oriented**: Use functional approach in C++ backend
2. **Memory Management**: Let nanobind handle Python-C++ object lifecycle
3. **Type System**: Use explicit Eigen types for matrices/arrays
4. **Error Handling**: Implement proper exception handling between C++ and Python

#### Testing Strategy
- Start each module with simple unit tests
- Use existing compas_occt tests as reference
- Validate API compatibility at each step

### Module Dependency Order
```
conversions/geometry.py  (START HERE - no dependencies)
    ↓
occ.py  (depends on conversions)
    ↓  
geometry/curves/  (depends on conversions + occ)
    ↓
geometry/surfaces/  (depends on curves)
    ↓
brep/  (depends on all above)
```

### Why Start with `conversions/geometry.py`?
1. **Minimal Dependencies**: Only depends on OCC.Core and compas.geometry
2. **Pure Functions**: Easy to test and validate
3. **Foundation Layer**: Everything else builds on these conversions  
4. **Incremental Progress**: You can test each conversion function independently
5. **Clear Success Criteria**: Easy to verify correctness

### Development Workflow
1. Pick one conversion function (e.g., `point_to_occ`)
2. Implement C++ version using nanobind
3. Create Python wrapper
4. Write unit test comparing with original
5. Repeat for next function
6. Move to next module when current is complete

This approach ensures you maintain API compatibility while building your own optimized implementation step by step.
