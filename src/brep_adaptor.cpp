// brep_adaptor.cpp - BRepAdaptor-based extractors backing OCCBrepEdge / OCCBrepFace.
//
// edge_type/face_type return the raw GeomAbs int, which matches compas.geometry.CurveType /
// SurfaceType one-to-one (Line=0..OtherCurve=7 ; Plane=0..OtherSurface=10). The 3D->plain-data
// tuples use the conversions vocabulary: circle=(frame,r), ellipse=(frame,major,minor),
// hyperbola=(frame,major,minor), parabola=(frame,focal), plane=(point,normal), etc.
#include "compas.h"
#include "occt.h"

#include <array>
#include <tuple>
#include <utility>

#include <TopoDS.hxx>
#include <BRep_Tool.hxx>
#include <BRepAdaptor_Curve.hxx>
#include <BRepAdaptor_Surface.hxx>
#include <Geom_BezierCurve.hxx>
#include <Geom_BSplineCurve.hxx>
#include <Geom_BSplineSurface.hxx>
#include <gp_Circ.hxx>
#include <gp_Elips.hxx>
#include <gp_Hypr.hxx>
#include <gp_Parab.hxx>
#include <gp_Pln.hxx>
#include <gp_Cylinder.hxx>
#include <gp_Cone.hxx>
#include <gp_Sphere.hxx>
#include <gp_Torus.hxx>

// ---------------------------------------------------------------------------
// edge adaptor
// ---------------------------------------------------------------------------

static int edge_type(const Shape& edge) {
    BRepAdaptor_Curve adaptor(TopoDS::Edge(edge.shape));
    return static_cast<int>(adaptor.GetType());
}

static std::pair<double, double> edge_domain(const Shape& edge) {
    BRepAdaptor_Curve adaptor(TopoDS::Edge(edge.shape));
    return {adaptor.FirstParameter(), adaptor.LastParameter()};
}

static std::pair<Ax, double> edge_to_circle(const Shape& edge) {
    BRepAdaptor_Curve adaptor(TopoDS::Edge(edge.shape));
    gp_Circ c = adaptor.Circle();
    return {from_ax2(c.Position()), c.Radius()};
}

static std::tuple<Ax, double, double> edge_to_ellipse(const Shape& edge) {
    BRepAdaptor_Curve adaptor(TopoDS::Edge(edge.shape));
    gp_Elips e = adaptor.Ellipse();
    return {from_ax2(e.Position()), e.MajorRadius(), e.MinorRadius()};
}

static std::tuple<Ax, double, double> edge_to_hyperbola(const Shape& edge) {
    BRepAdaptor_Curve adaptor(TopoDS::Edge(edge.shape));
    gp_Hypr h = adaptor.Hyperbola();
    return {from_ax2(h.Position()), h.MajorRadius(), h.MinorRadius()};
}

static std::pair<Ax, double> edge_to_parabola(const Shape& edge) {
    BRepAdaptor_Curve adaptor(TopoDS::Edge(edge.shape));
    gp_Parab p = adaptor.Parabola();
    return {from_ax2(p.Position()), p.Focal()};
}

static std::vector<Triple> edge_to_bezier(const Shape& edge) {
    BRepAdaptor_Curve adaptor(TopoDS::Edge(edge.shape));
    opencascade::handle<Geom_BezierCurve> bz = adaptor.Bezier();
    std::vector<Triple> out;
    out.reserve(bz->NbPoles());
    for (int i = 1; i <= bz->NbPoles(); ++i) out.push_back(from_pnt(bz->Pole(i)));
    return out;
}

static GeomCurve edge_to_bspline(const Shape& edge) {
    BRepAdaptor_Curve adaptor(TopoDS::Edge(edge.shape));
    return GeomCurve(adaptor.BSpline());
}

// ---------------------------------------------------------------------------
// face adaptor
// ---------------------------------------------------------------------------

static int face_type(const Shape& face) {
    BRepAdaptor_Surface adaptor(TopoDS::Face(face.shape));
    return static_cast<int>(adaptor.GetType());
}

// (point, normal)
static std::array<Triple, 2> face_to_plane(const Shape& face) {
    BRepAdaptor_Surface adaptor(TopoDS::Face(face.shape));
    gp_Pln pln = adaptor.Plane();
    return {from_pnt(pln.Location()), from_dir(pln.Axis().Direction())};
}

static std::pair<Ax, double> face_to_cylinder(const Shape& face) {
    BRepAdaptor_Surface adaptor(TopoDS::Face(face.shape));
    gp_Cylinder c = adaptor.Cylinder();
    return {from_ax3(c.Position()), c.Radius()};
}

// (frame, e2, e3): faithful to compas conversions ordering (ref-radius, semi-angle).
static std::tuple<Ax, double, double> face_to_cone(const Shape& face) {
    BRepAdaptor_Surface adaptor(TopoDS::Face(face.shape));
    gp_Cone c = adaptor.Cone();
    return {from_ax3(c.Position()), c.RefRadius(), c.SemiAngle()};
}

static std::pair<Ax, double> face_to_sphere(const Shape& face) {
    BRepAdaptor_Surface adaptor(TopoDS::Face(face.shape));
    gp_Sphere s = adaptor.Sphere();
    return {from_ax3(s.Position()), s.Radius()};
}

static std::tuple<Ax, double, double> face_to_torus(const Shape& face) {
    BRepAdaptor_Surface adaptor(TopoDS::Face(face.shape));
    gp_Torus t = adaptor.Torus();
    return {from_ax3(t.Position()), t.MajorRadius(), t.MinorRadius()};
}

static GeomSurface face_to_bspline(const Shape& face) {
    BRepAdaptor_Surface adaptor(TopoDS::Face(face.shape));
    return GeomSurface(adaptor.BSpline());
}

static GeomSurface face_surface(const Shape& face) {
    return GeomSurface(BRep_Tool::Surface(TopoDS::Face(face.shape)));
}

// (umin, umax, vmin, vmax)
static std::array<double, 4> face_domain(const Shape& face) {
    BRepAdaptor_Surface adaptor(TopoDS::Face(face.shape));
    return {adaptor.FirstUParameter(), adaptor.LastUParameter(),
            adaptor.FirstVParameter(), adaptor.LastVParameter()};
}

void register_adaptor(nb::module_& m) {
    m.def("edge_type", &edge_type);
    m.def("edge_domain", &edge_domain);
    m.def("edge_to_circle", &edge_to_circle);
    m.def("edge_to_ellipse", &edge_to_ellipse);
    m.def("edge_to_hyperbola", &edge_to_hyperbola);
    m.def("edge_to_parabola", &edge_to_parabola);
    m.def("edge_to_bezier", &edge_to_bezier);
    m.def("edge_to_bspline", &edge_to_bspline);
    m.def("face_type", &face_type);
    m.def("face_to_plane", &face_to_plane);
    m.def("face_to_cylinder", &face_to_cylinder);
    m.def("face_to_cone", &face_to_cone);
    m.def("face_to_sphere", &face_to_sphere);
    m.def("face_to_torus", &face_to_torus);
    m.def("face_to_bspline", &face_to_bspline);
    m.def("face_surface", &face_surface);
    m.def("face_domain", &face_domain);
}
