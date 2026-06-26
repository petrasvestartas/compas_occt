// surfaces.cpp - the `_surfaces` extension module: free functions backing OCCSurface
// and OCCNurbsSurface (nurbssurface.cpp).
#include "compas.h"
#include "occt.h"

#include <array>
#include <utility>

#include <Geom_Surface.hxx>
#include <Geom_Geometry.hxx>
#include <Geom_Line.hxx>
#include <GeomAdaptor_Surface.hxx>
#include <GeomAPI_IntCS.hxx>
#include <GeomAPI_ProjectPointOnSurf.hxx>
#include <GeomLProp_SLProps.hxx>
#include <Bnd_Box.hxx>
#include <Bnd_OBB.hxx>
#include <BndLib_AddSurface.hxx>
#include <BRepBndLib.hxx>
#include <BRep_Tool.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Face.hxx>
#include <gp_Lin.hxx>

static Shape surface_to_face(const GeomSurface& s) {
    return Shape(BRepBuilderAPI_MakeFace(s.surface, 1e-6).Shape());
}

static GeomSurface surface_from_face(const Shape& face) {
    opencascade::handle<Geom_Surface> srf = BRep_Tool::Surface(TopoDS::Face(face.shape));
    return GeomSurface(srf);
}

// (umin, umax, vmin, vmax)
static std::array<double, 4> surface_bounds(const GeomSurface& s) {
    double umin, umax, vmin, vmax;
    s.surface->Bounds(umin, umax, vmin, vmax);
    return {umin, umax, vmin, vmax};
}

static bool surface_is_periodic_u(const GeomSurface& s) { return s.surface->IsUPeriodic(); }
static bool surface_is_periodic_v(const GeomSurface& s) { return s.surface->IsVPeriodic(); }

static GeomSurface surface_copy(const GeomSurface& s) {
    return GeomSurface(opencascade::handle<Geom_Surface>::DownCast(s.surface->Copy()));
}

static void surface_transform(GeomSurface& s, const std::array<double, 12>& m) {
    s.surface->Transform(to_trsf(m));
}

static GeomCurve surface_uiso(const GeomSurface& s, double u) { return GeomCurve(s.surface->UIso(u)); }
static GeomCurve surface_viso(const GeomSurface& s, double v) { return GeomCurve(s.surface->VIso(v)); }

static Triple surface_point_at(const GeomSurface& s, double u, double v) {
    return from_pnt(s.surface->Value(u, v));
}

static Triple surface_normal_at(const GeomSurface& s, double u, double v) {
    GeomLProp_SLProps props(s.surface, u, v, 2, 1e-6);
    return from_dir(props.Normal());
}

static double surface_gaussian_curvature_at(const GeomSurface& s, double u, double v) {
    GeomLProp_SLProps props(s.surface, u, v, 2, 1e-6);
    return props.GaussianCurvature();
}

static double surface_mean_curvature_at(const GeomSurface& s, double u, double v) {
    GeomLProp_SLProps props(s.surface, u, v, 2, 1e-6);
    return props.MeanCurvature();
}

// (point, uvec, vvec)
static std::tuple<Triple, Triple, Triple> surface_frame_at(const GeomSurface& s, double u, double v) {
    gp_Pnt p;
    gp_Vec du, dv;
    s.surface->D1(u, v, p, du, dv);
    return {from_pnt(p), from_vec(du), from_vec(dv)};
}

static std::pair<Triple, Triple> surface_aabb(const GeomSurface& s, double precision, bool optimal) {
    Bnd_Box box;
    GeomAdaptor_Surface adaptor(s.surface);
    if (optimal)
        BndLib_AddSurface::AddOptimal(adaptor, precision, box);
    else
        BndLib_AddSurface::Add(adaptor, precision, box);
    return {from_pnt(box.CornerMin()), from_pnt(box.CornerMax())};
}

// (point, frame, xhsize, yhsize, zhsize); frame = (point, xaxis, yaxis)
static std::tuple<std::tuple<Triple, Triple, Triple>, double, double, double> surface_obb(const GeomSurface& s) {
    Bnd_OBB box;
    TopoDS_Shape face = BRepBuilderAPI_MakeFace(s.surface, 1e-6).Shape();
    BRepBndLib::AddOBB(face, box, Standard_True, Standard_True, Standard_True);
    const gp_Ax3 ax3 = box.Position();
    std::tuple<Triple, Triple, Triple> frame{from_pnt(ax3.Location()), from_dir(ax3.XDirection()), from_dir(ax3.YDirection())};
    return {frame, box.XHSize(), box.YHSize(), box.ZHSize()};
}

// (point, u, v)
static std::tuple<Triple, double, double> surface_closest_point(const GeomSurface& s, const Triple& point) {
    GeomAPI_ProjectPointOnSurf projector(to_pnt(point), s.surface);
    Triple nearest = from_pnt(projector.NearestPoint());
    double u, v;
    projector.LowerDistanceParameters(u, v);
    return {nearest, u, v};
}

static std::vector<Triple> surface_intersections_with_line(const GeomSurface& s, const Triple& loc, const Triple& dir) {
    opencascade::handle<Geom_Line> line = new Geom_Line(gp_Lin(to_pnt(loc), to_dir(dir)));
    GeomAPI_IntCS intersection(line, s.surface);
    std::vector<Triple> out;
    for (int i = 1; i <= intersection.NbPoints(); ++i) out.push_back(from_pnt(intersection.Point(i)));
    return out;
}

static std::vector<Triple> surface_intersections_with_curve(const GeomSurface& s, const GeomCurve& c) {
    GeomAPI_IntCS intersection(c.curve, s.surface);
    std::vector<Triple> out;
    for (int i = 1; i <= intersection.NbPoints(); ++i) out.push_back(from_pnt(intersection.Point(i)));
    return out;
}

void register_surfaces(nb::module_& m) {
    m.def("surface_to_face", &surface_to_face);
    m.def("surface_from_face", &surface_from_face);
    m.def("surface_bounds", &surface_bounds);
    m.def("surface_is_periodic_u", &surface_is_periodic_u);
    m.def("surface_is_periodic_v", &surface_is_periodic_v);
    m.def("surface_copy", &surface_copy);
    m.def("surface_transform", &surface_transform);
    m.def("surface_uiso", &surface_uiso);
    m.def("surface_viso", &surface_viso);
    m.def("surface_point_at", &surface_point_at);
    m.def("surface_normal_at", &surface_normal_at);
    m.def("surface_gaussian_curvature_at", &surface_gaussian_curvature_at);
    m.def("surface_mean_curvature_at", &surface_mean_curvature_at);
    m.def("surface_frame_at", &surface_frame_at);
    m.def("surface_aabb", &surface_aabb);
    m.def("surface_obb", &surface_obb);
    m.def("surface_closest_point", &surface_closest_point);
    m.def("surface_intersections_with_line", &surface_intersections_with_line);
    m.def("surface_intersections_with_curve", &surface_intersections_with_curve);
}

