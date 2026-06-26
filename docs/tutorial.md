# Tutorial

This tutorial gives a brief overview of the functionality of `compas_occt` and recommended best practices.


## Working with Curves

NURBS curves are created from control points (or from primitives such as lines, circles, and
ellipses) and can be evaluated and discretised anywhere in their parameter domain.

```python
from compas.geometry import Point
from compas_occt.geometry import OCCNurbsCurve

points = [Point(0, 0, 0), Point(3, 6, 0), Point(6, -3, 3), Point(10, 0, 0)]
curve = OCCNurbsCurve.from_points(points)

start, end = curve.domain
point = curve.point_at(0.5 * (start + end))
tangent = curve.tangent_at(0.5 * (start + end))
polyline = curve.to_polyline(n=100)
```


## Working with Surfaces

NURBS surfaces are created from a grid of control points and evaluated in their `(u, v)`
parameter space. Isocurves are returned as curves that can be discretised like any other.

```python
from compas.geometry import Point
from compas_occt.geometry import OCCNurbsSurface

points = [
    [Point(0, 0, 0), Point(1, 0, 0), Point(2, 0, 0)],
    [Point(0, 1, 0), Point(1, 1, 2), Point(2, 1, 0)],
    [Point(0, 2, 0), Point(1, 2, 0), Point(2, 2, 0)],
]
surface = OCCNurbsSurface.from_points(points=points)

point = surface.point_at(0.5, 0.5)
u_isocurve = surface.isocurve_u(0.5)
```


## Working with Breps

Breps (Boundary Representations) describe solids through their faces, edges, and vertices.
They are created from primitives or other geometry, queried for mass properties, and combined
with boolean operations (`+` union, `-` difference, `&` intersection).

```python
from compas.geometry import Box, Frame
from compas_occt.brep import OCCBrep

a = OCCBrep.from_box(Box(1))
b = OCCBrep.from_box(Box(1, frame=Frame([0.5, 0.5, 0.5])))

union = a + b

print(union.is_solid, union.volume, union.area)
```


## Visualisation

`compas_occt` geometry is visualised with [compas_viewer](https://github.com/compas-dev/compas_viewer).
Convert a Brep to its tessellated mesh and boundary curves, and add those to the viewer.

```python
from compas.geometry import Box
from compas_occt.brep import OCCBrep
from compas_viewer import Viewer

brep = OCCBrep.from_box(Box(1))
mesh, boundaries = brep.to_tesselation()

viewer = Viewer()
viewer.scene.add(mesh)
viewer.scene.add(boundaries)
viewer.show()
```


## Using the plugin system

`compas_occt` provides a NURBS and Brep (Boundary Representation) backend for COMPAS based on OpenCASCADE. Although it can be used as a standalone package, the recommended way to use it is through the plugin system. The following snippets accomplish the same thing, but the first uses `compas_occt` directly, and the second uses it as a plugin.

```python

from compas.geometry import Point
from compas_occt.geometry import OCCNurbsCurve

points = [
    Point(0, 0, 0),
    Point(3, 6, 0),
    Point(6, -3, 3),
    Point(10, 0, 0)
]

curve = OCCNurbsCurve.from_points(points)
```

```python

from compas.geometry import Point
from compas.geometry import NurbsCurve

points = [
    Point(0, 0, 0),
    Point(3, 6, 0),
    Point(6, -3, 3),
    Point(10, 0, 0)
]

curve = NurbsCurve.from_points(points)
```

The advantage of using the plugin system is that it allows COMPAS to automatically switch to different backends depending on the current environment without changing the script.
For example, when working in Rhino, the first script will throw an error, whereas the second script will work as expected by switching to RhinoCommon as a backend.
