// handles.h - Opaque OCCT handle wrappers shared across all compas_occt extension modules.
//
// nanobind cannot hold OCCT's intrusive `opencascade::handle<T>` smart pointer directly,
// so we never bind OCCT classes. Instead we wrap the handle/shape by value in a tiny POD
// struct and bind *that* as an opaque nanobind type (no geometric methods). Free functions
// take/return these wrappers plus plain data (doubles / std::array / std::vector / Eigen).
//
// These 4 wrappers cover the whole compas_occ surface:
//   - Shape       : any TopoDS_Shape (vertex/edge/wire/face/shell/solid/compound)
//   - GeomCurve   : a 3D Geom_Curve (down-cast to Geom_BSplineCurve etc. on demand)
//   - Geom2dCurve : a 2D Geom2d_Curve (surface-embedded p-curves)
//   - GeomSurface : a Geom_Surface (down-cast to Geom_BSplineSurface etc. on demand)
//
// register_types(m) registers them once in the single `_occt` module (see module.cpp).
#pragma once

#include <TopoDS_Shape.hxx>
#include <Geom_Curve.hxx>
#include <Geom2d_Curve.hxx>
#include <Geom_Surface.hxx>
#include <Standard_Handle.hxx>

struct Shape {
    TopoDS_Shape shape;
    Shape() = default;
    explicit Shape(const TopoDS_Shape& s) : shape(s) {}
};

struct GeomCurve {
    opencascade::handle<Geom_Curve> curve;
    GeomCurve() = default;
    explicit GeomCurve(const opencascade::handle<Geom_Curve>& c) : curve(c) {}
};

struct Geom2dCurve {
    opencascade::handle<Geom2d_Curve> curve;
    Geom2dCurve() = default;
    explicit Geom2dCurve(const opencascade::handle<Geom2d_Curve>& c) : curve(c) {}
};

struct GeomSurface {
    opencascade::handle<Geom_Surface> surface;
    GeomSurface() = default;
    explicit GeomSurface(const opencascade::handle<Geom_Surface>& s) : surface(s) {}
};
