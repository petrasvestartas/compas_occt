// curves.cpp - the `_curves` extension module: free functions backing OCCCurve,
// OCCNurbsCurve (nurbscurve.cpp) and OCCCurve2d (curve2d.cpp).
#include "compas.h"
#include "occt.h"

#include <optional>
#include <utility>
#include <stdexcept>
#include <string>

#include <Geom_Curve.hxx>
#include <Geom_Geometry.hxx>
#include <Geom_OffsetCurve.hxx>
#include <Geom_Surface.hxx>
#include <GeomAdaptor_Curve.hxx>
#include <GCPnts_AbscissaPoint.hxx>
#include <Bnd_Box.hxx>
#include <BndLib_Add3dCurve.hxx>
#include <GeomAPI_ProjectPointOnCurve.hxx>
#include <GeomAPI_ExtremaCurveCurve.hxx>
#include <GeomProjLib.hxx>
#include <BRepBuilderAPI_MakeEdge.hxx>

// ---------------------------------------------------------------------------
// OCCCurve (Geom_Curve)
// ---------------------------------------------------------------------------

static std::pair<double, double> curve_domain(const GeomCurve& c) {
    return {c.curve->FirstParameter(), c.curve->LastParameter()};
}

static bool curve_is_closed(const GeomCurve& c) { return c.curve->IsClosed(); }
static bool curve_is_periodic(const GeomCurve& c) { return c.curve->IsPeriodic(); }

static GeomCurve curve_copy(const GeomCurve& c) {
    return GeomCurve(opencascade::handle<Geom_Curve>::DownCast(c.curve->Copy()));
}

static void curve_transform(GeomCurve& c, const std::array<double, 12>& m) {
    c.curve->Transform(to_trsf(m));
}

static void curve_reverse(GeomCurve& c) { c.curve->Reverse(); }

// Bounds check folded into C++ (one nanobind call instead of a separate domain query).
// std::invalid_argument is translated to a Python ValueError by nanobind.
static inline void require_in_domain(const opencascade::handle<Geom_Curve>& c, double t) {
    if (t < c->FirstParameter() || t > c->LastParameter())
        throw std::invalid_argument("The parameter is not in the domain of the curve.");
}

static Triple curve_point_at(const GeomCurve& c, double t) {
    const double a = c.curve->FirstParameter(), b = c.curve->LastParameter();
    if (t < a || t > b)
        throw std::invalid_argument("The parameter is not in the domain of the curve. t = " + std::to_string(t) +
                                    ", domain: (" + std::to_string(a) + ", " + std::to_string(b) + ")");
    return from_pnt(c.curve->Value(t));
}

// Bulk evaluation -> zero-copy numpy (n,3); one call instead of n for discretisation.
static nb::ndarray<nb::numpy, double> curve_points_at(const GeomCurve& c, const std::vector<double>& ts) {
    std::vector<double> d;
    d.reserve(ts.size() * 3);
    for (double t : ts) {
        const gp_Pnt p = c.curve->Value(t);
        d.push_back(p.X());
        d.push_back(p.Y());
        d.push_back(p.Z());
    }
    return to_numpy(std::move(d), {ts.size(), 3});
}

static Triple curve_tangent_at(const GeomCurve& c, double t) {
    require_in_domain(c.curve, t);
    gp_Pnt p;
    gp_Vec u;
    c.curve->D1(t, p, u);
    return from_vec(u);
}

static Triple curve_curvature_at(const GeomCurve& c, double t) {
    require_in_domain(c.curve, t);
    gp_Pnt p;
    gp_Vec u, v;
    c.curve->D2(t, p, u, v);
    return from_vec(v);
}

// returns (point, uvec, vvec) for building a compas Frame
static std::tuple<Triple, Triple, Triple> curve_frame_at(const GeomCurve& c, double t) {
    require_in_domain(c.curve, t);
    gp_Pnt p;
    gp_Vec u, v;
    c.curve->D2(t, p, u, v);
    return {from_pnt(p), from_vec(u), from_vec(v)};
}

static double curve_parameter_at_distance(const GeomCurve& c, double t, double distance, double precision) {
    GeomAdaptor_Curve adaptor(c.curve);
    GCPnts_AbscissaPoint a(adaptor, distance, t, precision);
    return a.Parameter();
}

static std::pair<Triple, Triple> curve_aabb(const GeomCurve& c, double precision) {
    Bnd_Box box;
    GeomAdaptor_Curve adaptor(c.curve);
    BndLib_Add3dCurve::Add(adaptor, precision, box);
    return {from_pnt(box.CornerMin()), from_pnt(box.CornerMax())};
}

static double curve_length(const GeomCurve& c, double precision) {
    GeomAdaptor_Curve adaptor(c.curve);
    return GCPnts_AbscissaPoint::Length(adaptor, precision);
}

// (nearest point, parameter) or nullopt if the projection failed (start/end fallback in Python)
static std::optional<std::pair<Triple, double>> curve_closest_point(const GeomCurve& c, const Triple& point) {
    GeomAPI_ProjectPointOnCurve projector(to_pnt(point), c.curve);
    try {
        gp_Pnt np = projector.NearestPoint();
        return std::make_pair(from_pnt(np), projector.LowerDistanceParameter());
    } catch (const Standard_Failure&) {
        return std::nullopt;
    }
}

// (u, v, distance)
static std::tuple<double, double, double> curve_closest_parameters_curve(const GeomCurve& a, const GeomCurve& b) {
    GeomAPI_ExtremaCurveCurve extrema(a.curve, b.curve);
    double u = 0.0, v = 0.0;
    extrema.LowerDistanceParameters(u, v);
    return {u, v, extrema.LowerDistance()};
}

// (point_a, point_b, distance)
static std::tuple<Triple, Triple, double> curve_closest_points_curve(const GeomCurve& a, const GeomCurve& b) {
    gp_Pnt pa, pb;
    GeomAPI_ExtremaCurveCurve extrema(a.curve, b.curve);
    extrema.NearestPoints(pa, pb);
    return {from_pnt(pa), from_pnt(pb), extrema.LowerDistance()};
}

// abscissa division parameters (interior); Python prepends/appends domain ends + optional points
static std::vector<double> curve_abscissa_params(const GeomCurve& c, double length, int count, double precision) {
    GeomAdaptor_Curve adaptor(c.curve);
    std::vector<double> params;
    double t = c.curve->FirstParameter();
    for (int i = 0; i < count - 1; ++i) {
        GCPnts_AbscissaPoint a(adaptor, length, t, precision);
        t = a.Parameter();
        params.push_back(t);
    }
    return params;
}

static GeomCurve curve_projected(const GeomCurve& c, const GeomSurface& s) {
    return GeomCurve(GeomProjLib::Project(c.curve, s.surface));
}

static Geom2dCurve curve_embedded(const GeomCurve& c, const GeomSurface& s) {
    return Geom2dCurve(GeomProjLib::Curve2d(c.curve, s.surface));
}

static GeomCurve curve_offset(const GeomCurve& c, double distance, const Triple& direction) {
    opencascade::handle<Geom_OffsetCurve> oc = new Geom_OffsetCurve(c.curve, distance, to_dir(direction));
    return GeomCurve(oc);
}

static Shape curve_to_edge(const GeomCurve& c) {
    return Shape(BRepBuilderAPI_MakeEdge(c.curve).Shape());
}

void register_curves(nb::module_& m) {
    m.def("curve_domain", &curve_domain);
    m.def("curve_is_closed", &curve_is_closed);
    m.def("curve_is_periodic", &curve_is_periodic);
    m.def("curve_copy", &curve_copy);
    m.def("curve_transform", &curve_transform);
    m.def("curve_reverse", &curve_reverse);
    m.def("curve_point_at", &curve_point_at);
    m.def("curve_points_at", &curve_points_at);
    m.def("curve_tangent_at", &curve_tangent_at);
    m.def("curve_curvature_at", &curve_curvature_at);
    m.def("curve_frame_at", &curve_frame_at);
    m.def("curve_parameter_at_distance", &curve_parameter_at_distance);
    m.def("curve_aabb", &curve_aabb);
    m.def("curve_length", &curve_length);
    m.def("curve_closest_point", &curve_closest_point);
    m.def("curve_closest_parameters_curve", &curve_closest_parameters_curve);
    m.def("curve_closest_points_curve", &curve_closest_points_curve);
    m.def("curve_abscissa_params", &curve_abscissa_params);
    m.def("curve_projected", &curve_projected);
    m.def("curve_embedded", &curve_embedded);
    m.def("curve_offset", &curve_offset);
    m.def("curve_to_edge", &curve_to_edge);
}

