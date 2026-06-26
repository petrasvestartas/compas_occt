// curve2d.cpp - free functions backing OCCCurve2d (Geom2d_Curve), the 2D p-curves
// produced by embedding a 3D curve in a surface's parameter space.
#include "compas.h"
#include "occt.h"

#include <utility>
#include <stdexcept>
#include <string>

#include <Geom2d_Curve.hxx>
#include <Geom2d_Geometry.hxx>
#include <gp_Pnt2d.hxx>
#include <gp_Vec2d.hxx>
#include <BRepBuilderAPI_MakeEdge2d.hxx>

static std::pair<double, double> curve2d_domain(const Geom2dCurve& c) {
    return {c.curve->FirstParameter(), c.curve->LastParameter()};
}

static bool curve2d_is_closed(const Geom2dCurve& c) { return c.curve->IsClosed(); }
static bool curve2d_is_periodic(const Geom2dCurve& c) { return c.curve->IsPeriodic(); }

static Geom2dCurve curve2d_copy(const Geom2dCurve& c) {
    return Geom2dCurve(opencascade::handle<Geom2d_Curve>::DownCast(c.curve->Copy()));
}

// Bounds check folded into C++ (nanobind maps std::invalid_argument -> ValueError).
static inline void require_in_domain(const opencascade::handle<Geom2d_Curve>& c, double t) {
    if (t < c->FirstParameter() || t > c->LastParameter())
        throw std::invalid_argument("The parameter is not in the domain of the curve.");
}

static Triple curve2d_point_at(const Geom2dCurve& c, double t) {
    const double a = c.curve->FirstParameter(), b = c.curve->LastParameter();
    if (t < a || t > b)
        throw std::invalid_argument("The parameter is not in the domain of the curve. t = " + std::to_string(t) +
                                    ", domain: (" + std::to_string(a) + ", " + std::to_string(b) + ")");
    return from_pnt2d(c.curve->Value(t));
}

static Triple curve2d_tangent_at(const Geom2dCurve& c, double t) {
    require_in_domain(c.curve, t);
    gp_Pnt2d p;
    gp_Vec2d u;
    c.curve->D1(t, p, u);
    return {u.X(), u.Y(), 0.0};
}

static Triple curve2d_curvature_at(const Geom2dCurve& c, double t) {
    require_in_domain(c.curve, t);
    gp_Pnt2d p;
    gp_Vec2d u, v;
    c.curve->D2(t, p, u, v);
    return {v.X(), v.Y(), 0.0};
}

// (point, uvec, vvec) for a compas Frame
static std::tuple<Triple, Triple, Triple> curve2d_frame_at(const Geom2dCurve& c, double t) {
    require_in_domain(c.curve, t);
    gp_Pnt2d p;
    gp_Vec2d u, v;
    c.curve->D2(t, p, u, v);
    return {Triple{p.X(), p.Y(), 0.0}, Triple{u.X(), u.Y(), 0.0}, Triple{v.X(), v.Y(), 0.0}};
}

static Shape curve2d_to_edge(const Geom2dCurve& c) {
    return Shape(BRepBuilderAPI_MakeEdge2d(c.curve).Shape());
}

void register_curve2d(nb::module_& m) {
    m.def("curve2d_domain", &curve2d_domain);
    m.def("curve2d_is_closed", &curve2d_is_closed);
    m.def("curve2d_is_periodic", &curve2d_is_periodic);
    m.def("curve2d_copy", &curve2d_copy);
    m.def("curve2d_point_at", &curve2d_point_at);
    m.def("curve2d_tangent_at", &curve2d_tangent_at);
    m.def("curve2d_curvature_at", &curve2d_curvature_at);
    m.def("curve2d_frame_at", &curve2d_frame_at);
    m.def("curve2d_to_edge", &curve2d_to_edge);
}
