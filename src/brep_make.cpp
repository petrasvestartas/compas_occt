// brep_make.cpp - constructor free functions backing OCCBrep / OCCBrepVertex / OCCBrepEdge /
// OCCBrepLoop / OCCBrepFace factories and primitive makers.
#include "compas.h"
#include "occt.h"

#include <optional>
#include <utility>

#include <TopoDS.hxx>
#include <TopoDS_Shape.hxx>
#include <TopoDS_Vertex.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Wire.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Shell.hxx>
#include <TopoDS_Compound.hxx>

#include <gp_Lin.hxx>
#include <gp_Circ.hxx>
#include <gp_Elips.hxx>
#include <gp_Pln.hxx>
#include <gp_Cylinder.hxx>
#include <gp_Cone.hxx>
#include <gp_Sphere.hxx>
#include <gp_Torus.hxx>
#include <Geom_Circle.hxx>
#include <Geom_Ellipse.hxx>
#include <Geom_Plane.hxx>
#include <Geom_CylindricalSurface.hxx>
#include <Geom_SphericalSurface.hxx>
#include <TopAbs_Orientation.hxx>

#include <BRep_Builder.hxx>
#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepPrimAPI_MakeSphere.hxx>
#include <BRepPrimAPI_MakeCylinder.hxx>
#include <BRepPrimAPI_MakeCone.hxx>
#include <BRepPrimAPI_MakeTorus.hxx>
#include <BRepPrimAPI_MakePrism.hxx>
#include <BRepBuilderAPI_MakeVertex.hxx>
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepBuilderAPI_MakePolygon.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_Copy.hxx>
#include <BRepBuilderAPI_Transform.hxx>
#include <BRepBuilderAPI_NurbsConvert.hxx>
#include <BRepOffsetAPI_ThruSections.hxx>
#include <BRepOffsetAPI_MakePipe.hxx>

using Seg = std::array<Triple, 2>;            // (location, direction) or (point, normal)
using CircleData = std::pair<Ax, double>;     // (frame, radius)
using ConeData = std::tuple<Ax, double, double>;  // (frame, e2, e3)

using OptParams = std::optional<std::pair<double, double>>;
using OptPoints = std::optional<std::pair<Triple, Triple>>;
using OptVertices = std::optional<std::pair<Shape, Shape>>;

static TopoDS_Vertex as_vertex(const Shape& s) { return TopoDS::Vertex(s.shape); }
static TopoDS_Wire as_wire(const Shape& s) { return TopoDS::Wire(s.shape); }

// ---------------------------------------------------------------------------
// primitive solids
// ---------------------------------------------------------------------------

static Shape make_box(const Ax& frame, double xsize, double ysize, double zsize) {
    return Shape(BRepPrimAPI_MakeBox(to_ax2_from_frame(frame), xsize, ysize, zsize).Shape());
}

static Shape make_sphere(const Triple& center, double radius) {
    return Shape(BRepPrimAPI_MakeSphere(to_pnt(center), radius).Shape());
}

static Shape make_cylinder(const Ax& frame, double radius, double height) {
    gp_Ax2 ax2 = to_ax2_from_frame(frame);
    ax2.Translate(gp_Vec(ax2.Direction()) * (-0.5 * height));
    return Shape(BRepPrimAPI_MakeCylinder(ax2, radius, height).Shape());
}

static Shape make_cone(const Ax& frame, double r1, double r2, double height) {
    return Shape(BRepPrimAPI_MakeCone(to_ax2_from_frame(frame), r1, r2, height).Shape());
}

static Shape make_torus(const Ax& frame, double r_axis, double r_pipe) {
    return Shape(BRepPrimAPI_MakeTorus(to_ax2_from_frame(frame), r_axis, r_pipe).Shape());
}

// ---------------------------------------------------------------------------
// vertices / edges / wires
// ---------------------------------------------------------------------------

static Shape make_vertex(const Triple& point) {
    return Shape(BRepBuilderAPI_MakeVertex(to_pnt(point)).Vertex());
}

static Shape make_edge_vertex_vertex(const Shape& a, const Shape& b) {
    return Shape(BRepBuilderAPI_MakeEdge(as_vertex(a), as_vertex(b)).Edge());
}

static Shape make_edge_point_point(const Triple& a, const Triple& b) {
    return Shape(BRepBuilderAPI_MakeEdge(to_pnt(a), to_pnt(b)).Edge());
}

static Shape make_edge_line(const Seg& line, OptParams params, OptPoints points, OptVertices vertices) {
    gp_Lin lin(to_pnt(line[0]), to_dir(line[1]));
    if (params)
        return Shape(BRepBuilderAPI_MakeEdge(lin, params->first, params->second).Edge());
    if (points)
        return Shape(BRepBuilderAPI_MakeEdge(lin, to_pnt(points->first), to_pnt(points->second)).Edge());
    if (vertices)
        return Shape(BRepBuilderAPI_MakeEdge(lin, as_vertex(vertices->first), as_vertex(vertices->second)).Edge());
    return Shape(BRepBuilderAPI_MakeEdge(lin).Edge());
}

static Shape make_edge_circle(const CircleData& circle, OptParams params, OptPoints points, OptVertices vertices) {
    gp_Circ circ(to_ax2_from_frame(circle.first), circle.second);
    if (params)
        return Shape(BRepBuilderAPI_MakeEdge(circ, params->first, params->second).Edge());
    if (points)
        return Shape(BRepBuilderAPI_MakeEdge(circ, to_pnt(points->first), to_pnt(points->second)).Edge());
    if (vertices)
        return Shape(BRepBuilderAPI_MakeEdge(circ, as_vertex(vertices->first), as_vertex(vertices->second)).Edge());
    return Shape(BRepBuilderAPI_MakeEdge(circ).Edge());
}

static Shape make_edge_curve(const GeomCurve& curve, OptParams params, OptPoints points, OptVertices vertices) {
    if (points) {
        gp_Pnt p1 = to_pnt(points->first);
        gp_Pnt p2 = to_pnt(points->second);
        if (params)
            return Shape(BRepBuilderAPI_MakeEdge(curve.curve, p1, p2, params->first, params->second).Edge());
        return Shape(BRepBuilderAPI_MakeEdge(curve.curve, p1, p2).Edge());
    }
    if (vertices) {
        TopoDS_Vertex v1 = as_vertex(vertices->first);
        TopoDS_Vertex v2 = as_vertex(vertices->second);
        if (params)
            return Shape(BRepBuilderAPI_MakeEdge(curve.curve, v1, v2, params->first, params->second).Edge());
        return Shape(BRepBuilderAPI_MakeEdge(curve.curve, v1, v2).Edge());
    }
    if (params)
        return Shape(BRepBuilderAPI_MakeEdge(curve.curve, params->first, params->second).Edge());
    return Shape(BRepBuilderAPI_MakeEdge(curve.curve).Edge());
}

static Shape make_edge_curve2d_surface(const Geom2dCurve& curve, const GeomSurface& surface,
                                       OptParams params, OptPoints points, OptVertices vertices) {
    if (points) {
        gp_Pnt p1 = to_pnt(points->first);
        gp_Pnt p2 = to_pnt(points->second);
        if (params)
            return Shape(BRepBuilderAPI_MakeEdge(curve.curve, surface.surface, p1, p2, params->first, params->second).Edge());
        return Shape(BRepBuilderAPI_MakeEdge(curve.curve, surface.surface, p1, p2).Edge());
    }
    if (vertices) {
        TopoDS_Vertex v1 = as_vertex(vertices->first);
        TopoDS_Vertex v2 = as_vertex(vertices->second);
        if (params)
            return Shape(BRepBuilderAPI_MakeEdge(curve.curve, surface.surface, v1, v2, params->first, params->second).Edge());
        return Shape(BRepBuilderAPI_MakeEdge(curve.curve, surface.surface, v1, v2).Edge());
    }
    if (params)
        return Shape(BRepBuilderAPI_MakeEdge(curve.curve, surface.surface, params->first, params->second).Edge());
    return Shape(BRepBuilderAPI_MakeEdge(curve.curve, surface.surface).Edge());
}

static Shape make_wire(const std::vector<Shape>& edges) {
    BRepBuilderAPI_MakeWire builder;
    for (const auto& e : edges) builder.Add(TopoDS::Edge(e.shape));
    return Shape(builder.Wire());
}

// ---------------------------------------------------------------------------
// faces
// ---------------------------------------------------------------------------

static Shape make_face_polygon(const std::vector<Triple>& points) {
    BRepBuilderAPI_MakePolygon polygon;
    for (const auto& p : points) polygon.Add(to_pnt(p));
    polygon.Close();
    return Shape(BRepBuilderAPI_MakeFace(polygon.Wire()).Face());
}

static Shape make_face_plane(const Seg& plane, std::optional<std::array<double, 4>> domain,
                             std::optional<Shape> loop, bool inside) {
    gp_Pln pln(to_pnt(plane[0]), to_dir(plane[1]));
    if (domain)
        return Shape(BRepBuilderAPI_MakeFace(pln, (*domain)[0], (*domain)[1], (*domain)[2], (*domain)[3]).Face());
    if (loop)
        return Shape(BRepBuilderAPI_MakeFace(pln, as_wire(*loop), inside).Face());
    return Shape(BRepBuilderAPI_MakeFace(pln).Face());
}

static Shape make_face_cylinder(const CircleData& cyl, std::optional<Shape> loop, bool inside) {
    gp_Cylinder c(to_ax3_from_frame(cyl.first), cyl.second);
    if (loop)
        return Shape(BRepBuilderAPI_MakeFace(c, as_wire(*loop), inside).Face());
    return Shape(BRepBuilderAPI_MakeFace(c).Face());
}

static Shape make_face_cone(const ConeData& cone, std::optional<Shape> loop, bool inside) {
    gp_Cone c(to_ax3_from_frame(std::get<0>(cone)), std::get<1>(cone), std::get<2>(cone));
    if (loop)
        return Shape(BRepBuilderAPI_MakeFace(c, as_wire(*loop), inside).Face());
    return Shape(BRepBuilderAPI_MakeFace(c).Face());
}

static Shape make_face_sphere(const CircleData& sph, std::optional<Shape> loop, bool inside) {
    gp_Sphere s(to_ax3_from_frame(sph.first), sph.second);
    if (loop)
        return Shape(BRepBuilderAPI_MakeFace(s, as_wire(*loop), inside).Face());
    return Shape(BRepBuilderAPI_MakeFace(s).Face());
}

static Shape make_face_torus(const ConeData& tor, std::optional<Shape> loop, bool inside) {
    gp_Torus t(to_ax3_from_frame(std::get<0>(tor)), std::get<1>(tor), std::get<2>(tor));
    if (loop)
        return Shape(BRepBuilderAPI_MakeFace(t, as_wire(*loop), inside).Face());
    return Shape(BRepBuilderAPI_MakeFace(t).Face());
}

static Shape make_face_surface(const GeomSurface& surface, std::optional<std::array<double, 4>> domain,
                               double precision, std::optional<Shape> loop, bool inside) {
    if (domain)
        return Shape(BRepBuilderAPI_MakeFace(surface.surface, (*domain)[0], (*domain)[1], (*domain)[2], (*domain)[3], precision).Face());
    if (loop)
        return Shape(BRepBuilderAPI_MakeFace(surface.surface, as_wire(*loop), inside).Face());
    return Shape(BRepBuilderAPI_MakeFace(surface.surface, precision).Face());
}

static Shape face_add_loop(const Shape& face, const Shape& loop, bool reverse) {
    BRepBuilderAPI_MakeFace builder(TopoDS::Face(face.shape));
    if (reverse)
        builder.Add(TopoDS::Wire(loop.shape.Reversed()));
    else
        builder.Add(as_wire(loop));
    return Shape(builder.Face());
}

// ---------------------------------------------------------------------------
// derived shapes
// ---------------------------------------------------------------------------

static Shape make_prism(const Shape& profile, const Triple& vec) {
    return Shape(BRepPrimAPI_MakePrism(profile.shape, to_vec(vec)).Shape());
}

static Shape make_pipe(const Shape& spine, const Shape& profile) {
    return Shape(BRepOffsetAPI_MakePipe(as_wire(spine), profile.shape).Shape());
}

static Shape make_thrusections(const std::vector<Shape>& wires, bool solid, bool ruled) {
    BRepOffsetAPI_ThruSections thru(solid, ruled);
    for (const auto& w : wires) thru.AddWire(as_wire(w));
    thru.Build();
    return Shape(thru.Shape());
}

static Shape shell_from_faces(const std::vector<Shape>& faces) {
    TopoDS_Shell shell;
    BRep_Builder builder;
    builder.MakeShell(shell);
    for (const auto& f : faces) builder.Add(shell, TopoDS::Face(f.shape));
    return Shape(shell);
}

static Shape compound_from_shapes(const std::vector<Shape>& shapes) {
    TopoDS_Compound compound;
    BRep_Builder builder;
    builder.MakeCompound(compound);
    for (const auto& s : shapes) builder.Add(compound, s.shape);
    return Shape(compound);
}

static Shape copy_shape(const Shape& s) {
    BRepBuilderAPI_Copy builder(s.shape);
    builder.Perform(s.shape);
    return Shape(builder.Shape());
}

static Shape transform_shape(const Shape& s, const std::array<double, 12>& m, bool copy) {
    BRepBuilderAPI_Transform builder(s.shape, to_trsf(m), copy);
    return Shape(builder.ModifiedShape(s.shape));
}

static Shape nurbsconvert(const Shape& s) {
    BRepBuilderAPI_NurbsConvert converter(s.shape, Standard_False);
    return Shape(converter.Shape());
}

// ---------------------------------------------------------------------------
// primitive -> Geom_* handles (used by the serialization builder)
// ---------------------------------------------------------------------------

static GeomCurve geom_circle(const CircleData& c) {
    return GeomCurve(new Geom_Circle(gp_Circ(to_ax2_from_frame(c.first), c.second)));
}

static GeomCurve geom_ellipse(const ConeData& e) {
    return GeomCurve(new Geom_Ellipse(gp_Elips(to_ax2_from_frame(std::get<0>(e)), std::get<1>(e), std::get<2>(e))));
}

static GeomSurface geom_plane(const Seg& plane) {
    return GeomSurface(new Geom_Plane(gp_Pln(to_pnt(plane[0]), to_dir(plane[1]))));
}

static GeomSurface geom_cylinder(const CircleData& c) {
    return GeomSurface(new Geom_CylindricalSurface(gp_Cylinder(to_ax3_from_frame(c.first), c.second)));
}

static GeomSurface geom_sphere(const CircleData& s) {
    return GeomSurface(new Geom_SphericalSurface(gp_Sphere(to_ax3_from_frame(s.first), s.second)));
}

static Shape set_orientation(const Shape& s, int orientation) {
    return Shape(s.shape.Oriented(static_cast<TopAbs_Orientation>(orientation)));
}

void register_make(nb::module_& m) {
    m.def("make_box", &make_box);
    m.def("make_sphere", &make_sphere);
    m.def("make_cylinder", &make_cylinder);
    m.def("make_cone", &make_cone);
    m.def("make_torus", &make_torus);
    m.def("make_vertex", &make_vertex);
    m.def("make_edge_vertex_vertex", &make_edge_vertex_vertex);
    m.def("make_edge_point_point", &make_edge_point_point);
    m.def("make_edge_line", &make_edge_line, "line"_a, "params"_a = nb::none(), "points"_a = nb::none(), "vertices"_a = nb::none());
    m.def("make_edge_circle", &make_edge_circle, "circle"_a, "params"_a = nb::none(), "points"_a = nb::none(), "vertices"_a = nb::none());
    m.def("make_edge_curve", &make_edge_curve, "curve"_a, "params"_a = nb::none(), "points"_a = nb::none(), "vertices"_a = nb::none());
    m.def("make_edge_curve2d_surface", &make_edge_curve2d_surface, "curve"_a, "surface"_a, "params"_a = nb::none(), "points"_a = nb::none(), "vertices"_a = nb::none());
    m.def("make_wire", &make_wire);
    m.def("make_face_polygon", &make_face_polygon);
    m.def("make_face_plane", &make_face_plane, "plane"_a, "domain"_a = nb::none(), "loop"_a = nb::none(), "inside"_a = true);
    m.def("make_face_cylinder", &make_face_cylinder, "cylinder"_a, "loop"_a = nb::none(), "inside"_a = true);
    m.def("make_face_cone", &make_face_cone, "cone"_a, "loop"_a = nb::none(), "inside"_a = true);
    m.def("make_face_sphere", &make_face_sphere, "sphere"_a, "loop"_a = nb::none(), "inside"_a = true);
    m.def("make_face_torus", &make_face_torus, "torus"_a, "loop"_a = nb::none(), "inside"_a = true);
    m.def("make_face_surface", &make_face_surface, "surface"_a, "domain"_a = nb::none(), "precision"_a = 1e-6, "loop"_a = nb::none(), "inside"_a = true);
    m.def("face_add_loop", &face_add_loop, "face"_a, "loop"_a, "reverse"_a = false);
    m.def("make_prism", &make_prism);
    m.def("make_pipe", &make_pipe);
    m.def("make_thrusections", &make_thrusections, "wires"_a, "solid"_a = false, "ruled"_a = false);
    m.def("shell_from_faces", &shell_from_faces);
    m.def("compound_from_shapes", &compound_from_shapes);
    m.def("copy", &copy_shape);
    m.def("transform", &transform_shape, "shape"_a, "matrix"_a, "copy"_a = true);
    m.def("nurbsconvert", &nurbsconvert);
    m.def("geom_circle", &geom_circle);
    m.def("geom_ellipse", &geom_ellipse);
    m.def("geom_plane", &geom_plane);
    m.def("geom_cylinder", &geom_cylinder);
    m.def("geom_sphere", &geom_sphere);
    m.def("set_orientation", &set_orientation);
}
