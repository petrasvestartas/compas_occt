// types.cpp - register the 4 opaque OCCT handle wrappers in the _occt module.
#include "compas.h"
#include "handles.h"

void register_types(nb::module_& m) {
    nb::class_<Shape>(m, "Shape", "Opaque wrapper around an OCCT TopoDS_Shape.");
    nb::class_<GeomCurve>(m, "GeomCurve", "Opaque wrapper around an OCCT Geom_Curve handle.");
    nb::class_<Geom2dCurve>(m, "Geom2dCurve", "Opaque wrapper around an OCCT Geom2d_Curve handle.");
    nb::class_<GeomSurface>(m, "GeomSurface", "Opaque wrapper around an OCCT Geom_Surface handle.");
}

