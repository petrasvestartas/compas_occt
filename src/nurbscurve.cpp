// nurbscurve.cpp - free functions backing OCCNurbsCurve (Geom_BSplineCurve).
#include "compas.h"
#include "occt.h"

#include <utility>

#include <Geom_BSplineCurve.hxx>
#include <TColgp_Array1OfPnt.hxx>
#include <TColgp_HArray1OfPnt.hxx>
#include <TColStd_Array1OfReal.hxx>
#include <TColStd_Array1OfInteger.hxx>
#include <GeomAPI_Interpolate.hxx>
#include <GeomConvert_CompCurveToBSplineCurve.hxx>

static opencascade::handle<Geom_BSplineCurve> as_bspline(const GeomCurve& c) {
    return opencascade::handle<Geom_BSplineCurve>::DownCast(c.curve);
}

static GeomCurve nurbscurve_from_parameters(
    const std::vector<Triple>& points,
    const std::vector<double>& weights,
    const std::vector<double>& knots,
    const std::vector<int>& multiplicities,
    int degree,
    bool is_periodic) {
    const int np = static_cast<int>(points.size());
    const int nk = static_cast<int>(knots.size());

    TColgp_Array1OfPnt poles(1, np);
    TColStd_Array1OfReal w(1, np);
    for (int i = 0; i < np; ++i) {
        poles.SetValue(i + 1, to_pnt(points[i]));
        w.SetValue(i + 1, weights[i]);
    }
    TColStd_Array1OfReal k(1, nk);
    TColStd_Array1OfInteger m(1, nk);
    for (int i = 0; i < nk; ++i) {
        k.SetValue(i + 1, knots[i]);
        m.SetValue(i + 1, multiplicities[i]);
    }
    opencascade::handle<Geom_BSplineCurve> curve =
        new Geom_BSplineCurve(poles, w, k, m, degree, is_periodic);
    return GeomCurve(curve);
}

static GeomCurve nurbscurve_from_interpolation(const std::vector<Triple>& points, double precision) {
    const int np = static_cast<int>(points.size());
    opencascade::handle<TColgp_HArray1OfPnt> harray = new TColgp_HArray1OfPnt(1, np);
    for (int i = 0; i < np; ++i) harray->SetValue(i + 1, to_pnt(points[i]));
    GeomAPI_Interpolate interp(harray, Standard_False, precision);
    interp.Perform();
    return GeomCurve(interp.Curve());
}

static nb::ndarray<nb::numpy, double> nurbscurve_poles(const GeomCurve& c) {
    auto bs = as_bspline(c);
    const int n = bs->NbPoles();
    std::vector<double> d;
    d.reserve(static_cast<size_t>(n) * 3);
    for (int i = 1; i <= n; ++i) {
        const gp_Pnt p = bs->Pole(i);
        d.push_back(p.X());
        d.push_back(p.Y());
        d.push_back(p.Z());
    }
    return to_numpy(std::move(d), {static_cast<size_t>(n), 3});
}

static std::vector<double> nurbscurve_weights(const GeomCurve& c) {
    auto bs = as_bspline(c);
    std::vector<double> out;
    out.reserve(bs->NbPoles());
    for (int i = 1; i <= bs->NbPoles(); ++i) out.push_back(bs->Weight(i));
    return out;
}

static std::vector<double> nurbscurve_knots(const GeomCurve& c) {
    auto bs = as_bspline(c);
    std::vector<double> out;
    out.reserve(bs->NbKnots());
    for (int i = 1; i <= bs->NbKnots(); ++i) out.push_back(bs->Knot(i));
    return out;
}

static std::vector<double> nurbscurve_knotsequence(const GeomCurve& c) {
    auto bs = as_bspline(c);
    const TColStd_Array1OfReal& ks = bs->KnotSequence();
    std::vector<double> out;
    out.reserve(ks.Length());
    for (int i = ks.Lower(); i <= ks.Upper(); ++i) out.push_back(ks.Value(i));
    return out;
}

static std::vector<int> nurbscurve_multiplicities(const GeomCurve& c) {
    auto bs = as_bspline(c);
    std::vector<int> out;
    out.reserve(bs->NbKnots());
    for (int i = 1; i <= bs->NbKnots(); ++i) out.push_back(bs->Multiplicity(i));
    return out;
}

static Triple nurbscurve_start(const GeomCurve& c) { return from_pnt(as_bspline(c)->StartPoint()); }
static Triple nurbscurve_end(const GeomCurve& c) { return from_pnt(as_bspline(c)->EndPoint()); }
static int nurbscurve_continuity(const GeomCurve& c) { return static_cast<int>(as_bspline(c)->Continuity()); }
static int nurbscurve_degree(const GeomCurve& c) { return as_bspline(c)->Degree(); }
static bool nurbscurve_is_rational(const GeomCurve& c) { return as_bspline(c)->IsRational(); }

static void nurbscurve_segment(GeomCurve& c, double u, double v, double precision) {
    as_bspline(c)->Segment(u, v, precision);
}

// (joined curve, success). On failure returns the original handle and false.
static std::pair<GeomCurve, bool> nurbscurve_join(const GeomCurve& self, const GeomCurve& other, double precision) {
    GeomConvert_CompCurveToBSplineCurve converter(as_bspline(self));
    bool success = converter.Add(as_bspline(other), precision);
    if (success) return {GeomCurve(converter.BSplineCurve()), true};
    return {self, false};
}

void register_nurbscurve(nb::module_& m) {
    m.def("nurbscurve_from_parameters", &nurbscurve_from_parameters);
    m.def("nurbscurve_from_interpolation", &nurbscurve_from_interpolation);
    m.def("nurbscurve_poles", &nurbscurve_poles);
    m.def("nurbscurve_weights", &nurbscurve_weights);
    m.def("nurbscurve_knots", &nurbscurve_knots);
    m.def("nurbscurve_knotsequence", &nurbscurve_knotsequence);
    m.def("nurbscurve_multiplicities", &nurbscurve_multiplicities);
    m.def("nurbscurve_start", &nurbscurve_start);
    m.def("nurbscurve_end", &nurbscurve_end);
    m.def("nurbscurve_continuity", &nurbscurve_continuity);
    m.def("nurbscurve_degree", &nurbscurve_degree);
    m.def("nurbscurve_is_rational", &nurbscurve_is_rational);
    m.def("nurbscurve_segment", &nurbscurve_segment);
    m.def("nurbscurve_join", &nurbscurve_join);
}
