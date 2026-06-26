// nurbssurface.cpp - free functions backing OCCNurbsSurface (Geom_BSplineSurface) and
// the ControlPoints helper.
//
// Pole-grid layout convention (must match compas_occ's points2_from_array2(Poles())):
//   poles2 has shape [NbVPoles][NbUPoles] with poles2[v][u] == Pole(u+1, v+1).
//   from_parameters receives the user grid in the same [v][u] layout.
#include "compas.h"
#include "occt.h"

#include <Geom_BSplineSurface.hxx>
#include <Geom_Plane.hxx>
#include <TColgp_Array2OfPnt.hxx>
#include <TColStd_Array2OfReal.hxx>
#include <TColStd_Array1OfReal.hxx>
#include <TColStd_Array1OfInteger.hxx>
#include <GeomAbs_Shape.hxx>
#include <GeomAPI_PointsToBSplineSurface.hxx>
#include <GeomFill_BSplineCurves.hxx>
#include <GeomFill_FillingStyle.hxx>
#include <Geom_BSplineCurve.hxx>
#include <gp_Pln.hxx>

using Grid = std::vector<std::vector<Triple>>;
using FGrid = std::vector<std::vector<double>>;

static opencascade::handle<Geom_BSplineSurface> as_bspline(const GeomSurface& s) {
    return opencascade::handle<Geom_BSplineSurface>::DownCast(s.surface);
}

static opencascade::handle<Geom_BSplineCurve> curve_as_bspline(const GeomCurve& c) {
    return opencascade::handle<Geom_BSplineCurve>::DownCast(c.curve);
}

// Build a (1..nu, 1..nv) pole array from a [v][u] user grid.
static TColgp_Array2OfPnt poles_from_grid(const Grid& points) {
    const int nv = static_cast<int>(points.size());
    const int nu = static_cast<int>(points[0].size());
    TColgp_Array2OfPnt poles(1, nu, 1, nv);
    for (int v = 0; v < nv; ++v)
        for (int u = 0; u < nu; ++u)
            poles.SetValue(u + 1, v + 1, to_pnt(points[v][u]));
    return poles;
}

static GeomSurface nurbssurface_from_parameters(
    const Grid& points,
    const FGrid& weights,
    const std::vector<double>& knots_u,
    const std::vector<double>& knots_v,
    const std::vector<int>& mults_u,
    const std::vector<int>& mults_v,
    int degree_u,
    int degree_v,
    bool is_periodic_u,
    bool is_periodic_v) {
    const int nv = static_cast<int>(points.size());
    const int nu = static_cast<int>(points[0].size());

    TColgp_Array2OfPnt poles = poles_from_grid(points);
    TColStd_Array2OfReal w(1, nu, 1, nv);
    for (int v = 0; v < nv; ++v)
        for (int u = 0; u < nu; ++u)
            w.SetValue(u + 1, v + 1, weights[v][u]);

    TColStd_Array1OfReal uk(1, static_cast<int>(knots_u.size()));
    TColStd_Array1OfInteger um(1, static_cast<int>(mults_u.size()));
    for (int i = 0; i < static_cast<int>(knots_u.size()); ++i) {
        uk.SetValue(i + 1, knots_u[i]);
        um.SetValue(i + 1, mults_u[i]);
    }
    TColStd_Array1OfReal vk(1, static_cast<int>(knots_v.size()));
    TColStd_Array1OfInteger vm(1, static_cast<int>(mults_v.size()));
    for (int i = 0; i < static_cast<int>(knots_v.size()); ++i) {
        vk.SetValue(i + 1, knots_v[i]);
        vm.SetValue(i + 1, mults_v[i]);
    }

    opencascade::handle<Geom_BSplineSurface> srf =
        new Geom_BSplineSurface(poles, w, uk, vk, um, vm, degree_u, degree_v, is_periodic_u, is_periodic_v);
    return GeomSurface(srf);
}

static GeomSurface nurbssurface_from_interpolation(const Grid& points, double precision) {
    TColgp_Array2OfPnt poles = poles_from_grid(points);
    GeomAPI_PointsToBSplineSurface builder(poles, 3, 8, GeomAbs_C2, precision);
    return GeomSurface(builder.Surface());
}

static GeomSurface nurbssurface_from_plane(const Triple& point, const Triple& normal) {
    opencascade::handle<Geom_Plane> plane = new Geom_Plane(gp_Pln(to_pnt(point), to_dir(normal)));
    return GeomSurface(plane);
}

static GeomSurface nurbssurface_from_fill(const std::vector<GeomCurve>& curves, const std::string& style) {
    GeomFill_FillingStyle occ_style = GeomFill_StretchStyle;
    if (style == "coons")
        occ_style = GeomFill_CoonsStyle;
    else if (style == "curved")
        occ_style = GeomFill_CurvedStyle;

    GeomFill_BSplineCurves fill;
    if (curves.size() == 4) {
        fill = GeomFill_BSplineCurves(curve_as_bspline(curves[0]), curve_as_bspline(curves[1]),
                                      curve_as_bspline(curves[2]), curve_as_bspline(curves[3]), occ_style);
    } else if (curves.size() == 3) {
        fill = GeomFill_BSplineCurves(curve_as_bspline(curves[0]), curve_as_bspline(curves[1]),
                                      curve_as_bspline(curves[2]), occ_style);
    } else {
        fill = GeomFill_BSplineCurves(curve_as_bspline(curves[0]), curve_as_bspline(curves[1]), occ_style);
    }
    return GeomSurface(fill.Surface());
}

// poles2[v][u] = Pole(u+1, v+1) -> zero-copy numpy array of shape (NbVPoles, NbUPoles, 3)
static nb::ndarray<nb::numpy, double> nurbssurface_poles2(const GeomSurface& s) {
    auto bs = as_bspline(s);
    const int nu = bs->NbUPoles();
    const int nv = bs->NbVPoles();
    std::vector<double> d;
    d.reserve(static_cast<size_t>(nv) * nu * 3);
    for (int v = 1; v <= nv; ++v)
        for (int u = 1; u <= nu; ++u) {
            const gp_Pnt p = bs->Pole(u, v);
            d.push_back(p.X());
            d.push_back(p.Y());
            d.push_back(p.Z());
        }
    return to_numpy(std::move(d), {static_cast<size_t>(nv), static_cast<size_t>(nu), 3});
}

// weights2[v][u] = Weight(u+1, v+1) (1.0 for non-rational), shape [NbVPoles][NbUPoles]
static FGrid nurbssurface_weights2(const GeomSurface& s) {
    auto bs = as_bspline(s);
    const int nu = bs->NbUPoles();
    const int nv = bs->NbVPoles();
    FGrid out(nv, std::vector<double>(nu));
    for (int v = 1; v <= nv; ++v)
        for (int u = 1; u <= nu; ++u)
            out[v - 1][u - 1] = bs->Weight(u, v);
    return out;
}

static Triple nurbssurface_pole(const GeomSurface& s, int u, int v) {
    return from_pnt(as_bspline(s)->Pole(u, v));
}

static void nurbssurface_set_pole(GeomSurface& s, int u, int v, const Triple& point) {
    as_bspline(s)->SetPole(u, v, to_pnt(point));
}

static int nurbssurface_nb_upoles(const GeomSurface& s) { return as_bspline(s)->NbUPoles(); }
static int nurbssurface_nb_vpoles(const GeomSurface& s) { return as_bspline(s)->NbVPoles(); }
static int nurbssurface_degree_u(const GeomSurface& s) { return as_bspline(s)->UDegree(); }
static int nurbssurface_degree_v(const GeomSurface& s) { return as_bspline(s)->VDegree(); }

static std::vector<double> nurbssurface_uknots(const GeomSurface& s) {
    auto bs = as_bspline(s);
    std::vector<double> out;
    for (int i = 1; i <= bs->NbUKnots(); ++i) out.push_back(bs->UKnot(i));
    return out;
}
static std::vector<double> nurbssurface_vknots(const GeomSurface& s) {
    auto bs = as_bspline(s);
    std::vector<double> out;
    for (int i = 1; i <= bs->NbVKnots(); ++i) out.push_back(bs->VKnot(i));
    return out;
}
static std::vector<int> nurbssurface_umults(const GeomSurface& s) {
    auto bs = as_bspline(s);
    std::vector<int> out;
    for (int i = 1; i <= bs->NbUKnots(); ++i) out.push_back(bs->UMultiplicity(i));
    return out;
}
static std::vector<int> nurbssurface_vmults(const GeomSurface& s) {
    auto bs = as_bspline(s);
    std::vector<int> out;
    for (int i = 1; i <= bs->NbVKnots(); ++i) out.push_back(bs->VMultiplicity(i));
    return out;
}
static bool nurbssurface_is_rational(const GeomSurface& s) {
    auto bs = as_bspline(s);
    return bs->IsURational() || bs->IsVRational();
}

void register_nurbssurface(nb::module_& m) {
    m.def("nurbssurface_from_parameters", &nurbssurface_from_parameters);
    m.def("nurbssurface_from_interpolation", &nurbssurface_from_interpolation);
    m.def("nurbssurface_from_plane", &nurbssurface_from_plane);
    m.def("nurbssurface_from_fill", &nurbssurface_from_fill);
    m.def("nurbssurface_poles2", &nurbssurface_poles2);
    m.def("nurbssurface_weights2", &nurbssurface_weights2);
    m.def("nurbssurface_pole", &nurbssurface_pole);
    m.def("nurbssurface_set_pole", &nurbssurface_set_pole);
    m.def("nurbssurface_nb_upoles", &nurbssurface_nb_upoles);
    m.def("nurbssurface_nb_vpoles", &nurbssurface_nb_vpoles);
    m.def("nurbssurface_degree_u", &nurbssurface_degree_u);
    m.def("nurbssurface_degree_v", &nurbssurface_degree_v);
    m.def("nurbssurface_uknots", &nurbssurface_uknots);
    m.def("nurbssurface_vknots", &nurbssurface_vknots);
    m.def("nurbssurface_umults", &nurbssurface_umults);
    m.def("nurbssurface_vmults", &nurbssurface_vmults);
    m.def("nurbssurface_is_rational", &nurbssurface_is_rational);
}
