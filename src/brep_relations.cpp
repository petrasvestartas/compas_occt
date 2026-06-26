// brep_relations.cpp - topological adjacency queries backing OCCBrep.vertex_edges /
// vertex_faces / edge_faces / edge_loops / vertex_neighbors.
#include "compas.h"
#include "occt.h"

#include <TopAbs_ShapeEnum.hxx>
#include <TopExp.hxx>
#include <TopTools_IndexedDataMapOfShapeListOfShape.hxx>
#include <TopTools_ListOfShape.hxx>

// Return the `to_topabs` ancestors of sub-shape `sub` within `parent`, in the order produced
// by TopExp::MapShapesAndUniqueAncestors (matching OCCBrep's *_edges/*_faces/*_loops semantics).
static std::vector<Shape> ancestors(const Shape& parent, const Shape& sub, int from_topabs, int to_topabs) {
    TopTools_IndexedDataMapOfShapeListOfShape map;
    TopExp::MapShapesAndUniqueAncestors(parent.shape,
                                        static_cast<TopAbs_ShapeEnum>(from_topabs),
                                        static_cast<TopAbs_ShapeEnum>(to_topabs),
                                        map);
    std::vector<Shape> out;
    if (!map.Contains(sub.shape)) return out;
    const TopTools_ListOfShape& results = map.FindFromKey(sub.shape);
    for (TopTools_ListOfShape::Iterator it(results); it.More(); it.Next()) {
        out.push_back(Shape(it.Value()));
    }
    return out;
}

void register_relations(nb::module_& m) {
    m.def("ancestors", &ancestors);
}
