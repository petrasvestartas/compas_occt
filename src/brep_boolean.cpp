// brep_boolean.cpp - boolean / section / split / fillet / offset / overlap free functions.
// On failure (IsDone() == false) these throw std::runtime_error; the Python layer translates
// that into BrepBooleanError / BrepFilletError to match compas_occ.
#include "compas.h"
#include "occt.h"

#include <stdexcept>
#include <utility>

#include <TopoDS.hxx>
#include <TopoDS_Compound.hxx>
#include <TopoDS_Iterator.hxx>
#include <TopExp_Explorer.hxx>
#include <TopAbs_ShapeEnum.hxx>
#include <TopTools_ListOfShape.hxx>
#include <BRepAlgoAPI_Fuse.hxx>
#include <BRepAlgoAPI_Cut.hxx>
#include <BRepAlgoAPI_Common.hxx>
#include <BRepAlgoAPI_Section.hxx>
#include <BOPAlgo_Splitter.hxx>
#include <BRepFilletAPI_MakeFillet.hxx>
#include <BRepOffsetAPI_MakeThickSolid.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <BRepExtrema_ShapeProximity.hxx>
#include <NCollection_DataMap.hxx>
#include <TColStd_PackedMapOfInteger.hxx>

static TopTools_ListOfShape to_list(const std::vector<Shape>& shapes) {
    TopTools_ListOfShape L;
    for (const auto& s : shapes) L.Append(s.shape);
    return L;
}

static Shape boolean_union(const std::vector<Shape>& A, const std::vector<Shape>& B, double fuzzy) {
    BRepAlgoAPI_Fuse op;
    TopTools_ListOfShape LA = to_list(A);
    TopTools_ListOfShape LB = to_list(B);
    op.SetArguments(LA);
    op.SetTools(LB);
    op.SetFuzzyValue(fuzzy);
    op.SetRunParallel(Standard_False);
    op.Build();
    if (!op.IsDone()) throw std::runtime_error("Boolean fuse operation could not be completed.");
    return Shape(op.Shape());
}

static Shape boolean_difference(const std::vector<Shape>& A, const std::vector<Shape>& B, double fuzzy) {
    BRepAlgoAPI_Cut op;
    TopTools_ListOfShape LA = to_list(A);
    TopTools_ListOfShape LB = to_list(B);
    op.SetArguments(LA);
    op.SetTools(LB);
    op.SetFuzzyValue(fuzzy);
    op.SetRunParallel(Standard_False);
    op.Build();
    if (!op.IsDone()) throw std::runtime_error("Boolean difference operation could not be completed.");
    return Shape(op.Shape());
}

static Shape boolean_intersection(const std::vector<Shape>& A, const std::vector<Shape>& B, double fuzzy) {
    BRepAlgoAPI_Common op;
    TopTools_ListOfShape LA = to_list(A);
    TopTools_ListOfShape LB = to_list(B);
    op.SetArguments(LA);
    op.SetTools(LB);
    op.SetFuzzyValue(fuzzy);
    op.SetRunParallel(Standard_False);
    op.Build();
    if (!op.IsDone()) throw std::runtime_error("Boolean intersection operation could not be completed.");
    return Shape(op.Shape());
}

// Returns the section shape (an edge/wire compound) or throws if not done.
static Shape section(const Shape& a, const Shape& b) {
    BRepAlgoAPI_Section op(a.shape, b.shape);
    op.Build();
    if (!op.IsDone()) throw std::runtime_error("Section operation could not be completed.");
    return Shape(op.Shape());
}

// Split `arguments` by `tools`; expands the resulting compound into a flat list (matching occ.split_shapes).
static std::vector<Shape> split(const std::vector<Shape>& arguments, const std::vector<Shape>& tools) {
    BOPAlgo_Splitter splitter;
    for (const auto& s : arguments) splitter.AddArgument(s.shape);
    for (const auto& s : tools) splitter.AddTool(s.shape);
    splitter.Perform();
    TopoDS_Shape shape = splitter.Shape();
    std::vector<Shape> out;
    if (shape.ShapeType() == TopAbs_COMPOUND) {
        for (TopoDS_Iterator it(shape); it.More(); it.Next()) out.push_back(Shape(it.Value()));
    } else {
        out.push_back(Shape(shape));
    }
    return out;
}

static Shape fillet(const Shape& s, double radius, const std::vector<Shape>& exclude) {
    BRepFilletAPI_MakeFillet builder(s.shape);
    for (TopExp_Explorer explorer(s.shape, TopAbs_EDGE); explorer.More(); explorer.Next()) {
        const TopoDS_Shape& edge = explorer.Current();
        bool skip = false;
        for (const auto& e : exclude) {
            if (e.shape.IsSame(edge)) { skip = true; break; }
        }
        if (skip) continue;
        builder.Add(radius, TopoDS::Edge(edge));
    }
    builder.Build();
    if (!builder.IsDone()) throw std::runtime_error("Fillet operation could not be completed.");
    return Shape(builder.Shape());
}

static Shape offset(const Shape& s, double distance) {
    BRepOffsetAPI_MakeThickSolid builder;
    builder.MakeThickSolidBySimple(s.shape, distance);
    return Shape(builder.Shape());
}

// (faces_on_self, faces_on_other) that overlap within tolerance.
// In OCCT 8.0, OverlapSubShapes1/2() return NCollection_DataMap<int, TColStd_PackedMapOfInteger>
// (the BRepExtrema_MapOfIntegerPackedMapOfInteger typedef was removed) and GetSubShape1/2 return
// a TopoDS_Shape.
static std::pair<std::vector<Shape>, std::vector<Shape>> overlap(
    const Shape& a, const Shape& b, double linear, double angular, bool relative, double tolerance) {
    using ProxMap = NCollection_DataMap<int, TColStd_PackedMapOfInteger>;

    // The 5-arg constructor already meshes the shape (it auto-calls Perform), so an explicit
    // Perform() here would triangulate each shape a second time. Constructing the meshers is
    // enough; the triangulation is stored on the shape for BRepExtrema_ShapeProximity to use.
    BRepMesh_IncrementalMesh mesher1(a.shape, linear, relative, angular, Standard_False);
    BRepMesh_IncrementalMesh mesher2(b.shape, linear, relative, angular, Standard_False);

    BRepExtrema_ShapeProximity proximity(a.shape, b.shape, tolerance);
    proximity.Perform();

    std::vector<Shape> faces1;
    const ProxMap& m1 = proximity.OverlapSubShapes1();
    for (ProxMap::Iterator it(m1); it.More(); it.Next()) {
        faces1.push_back(Shape(proximity.GetSubShape1(it.Key())));
    }

    std::vector<Shape> faces2;
    const ProxMap& m2 = proximity.OverlapSubShapes2();
    for (ProxMap::Iterator it(m2); it.More(); it.Next()) {
        faces2.push_back(Shape(proximity.GetSubShape2(it.Key())));
    }

    return {faces1, faces2};
}

void register_boolean(nb::module_& m) {
    // These OCCT operations are long-running and operate purely on C++ data (no Python
    // callbacks), so release the GIL for the duration -> callers can run many of them in
    // parallel threads. No effect on single-threaded use.
    using gil = nb::call_guard<nb::gil_scoped_release>;
    m.def("boolean_union", &boolean_union, gil());
    m.def("boolean_difference", &boolean_difference, gil());
    m.def("boolean_intersection", &boolean_intersection, gil());
    m.def("section", &section, gil());
    m.def("split", &split, gil());
    m.def("fillet", &fillet, gil());
    m.def("offset", &offset, gil());
    m.def("overlap", &overlap, gil());
}
