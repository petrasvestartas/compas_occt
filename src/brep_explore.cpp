// brep_explore.cpp - topology exploration free functions backing OCCBrep* iteration.
#include "compas.h"
#include "occt.h"

#include <TopoDS.hxx>
#include <TopoDS_Shape.hxx>
#include <TopoDS_Vertex.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Wire.hxx>
#include <TopoDS_Shell.hxx>
#include <TopoDS_Solid.hxx>
#include <TopoDS_Compound.hxx>
#include <TopoDS_Iterator.hxx>
#include <TopExp.hxx>
#include <TopExp_Explorer.hxx>
#include <TopAbs_ShapeEnum.hxx>
#include <BRep_Tool.hxx>
#include <BRepTools.hxx>
#include <BRepTools_WireExplorer.hxx>

// TopAbs_ShapeEnum ints (verified against TopAbs_ShapeEnum.hxx):
//   COMPOUND=0, COMPSOLID=1, SOLID=2, SHELL=3, FACE=4, WIRE=5, EDGE=6, VERTEX=7, SHAPE=8.

static std::vector<Shape> shape_explore(const Shape& s, int topabs) {
    std::vector<Shape> out;
    TopExp_Explorer explorer(s.shape, static_cast<TopAbs_ShapeEnum>(topabs));
    while (explorer.More()) {
        out.push_back(Shape(explorer.Current()));
        explorer.Next();
    }
    return out;
}

static int shape_type(const Shape& s) { return static_cast<int>(s.shape.ShapeType()); }
static int shape_orientation(const Shape& s) { return static_cast<int>(s.shape.Orientation()); }
static bool shape_is_same(const Shape& a, const Shape& b) { return a.shape.IsSame(b.shape); }
static bool shape_is_equal(const Shape& a, const Shape& b) { return a.shape.IsEqual(b.shape); }

static std::vector<Shape> wire_explore_vertices(const Shape& wire) {
    std::vector<Shape> out;
    BRepTools_WireExplorer explorer(TopoDS::Wire(wire.shape));
    while (explorer.More()) {
        out.push_back(Shape(explorer.CurrentVertex()));
        explorer.Next();
    }
    return out;
}

static std::vector<Shape> wire_explore_edges(const Shape& wire) {
    std::vector<Shape> out;
    BRepTools_WireExplorer explorer(TopoDS::Wire(wire.shape));
    while (explorer.More()) {
        out.push_back(Shape(explorer.Current()));
        explorer.Next();
    }
    return out;
}

static Shape edge_first_vertex(const Shape& edge) {
    return Shape(TopExp::FirstVertex(TopoDS::Edge(edge.shape)));
}
static Shape edge_last_vertex(const Shape& edge) {
    return Shape(TopExp::LastVertex(TopoDS::Edge(edge.shape)));
}

static Triple vertex_point(const Shape& vertex) {
    return from_pnt(BRep_Tool::Pnt(TopoDS::Vertex(vertex.shape)));
}

static std::vector<Shape> shape_iterator_children(const Shape& s) {
    std::vector<Shape> out;
    for (TopoDS_Iterator it(s.shape); it.More(); it.Next()) {
        out.push_back(Shape(it.Value()));
    }
    return out;
}

static Shape outer_wire(const Shape& face) {
    return Shape(BRepTools::OuterWire(TopoDS::Face(face.shape)));
}

void register_explore(nb::module_& m) {
    m.def("shape_explore", &shape_explore);
    m.def("shape_type", &shape_type);
    m.def("shape_orientation", &shape_orientation);
    m.def("shape_is_same", &shape_is_same);
    m.def("shape_is_equal", &shape_is_equal);
    m.def("wire_explore_vertices", &wire_explore_vertices);
    m.def("wire_explore_edges", &wire_explore_edges);
    m.def("edge_first_vertex", &edge_first_vertex);
    m.def("edge_last_vertex", &edge_last_vertex);
    m.def("vertex_point", &vertex_point);
    m.def("shape_iterator_children", &shape_iterator_children);
    m.def("outer_wire", &outer_wire);
}

