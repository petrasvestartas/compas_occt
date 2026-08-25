// meshing.cpp - the `_meshing` extension module.
//
// Reimplements tessellation on BRepMesh (the OCCT Visualization module / ShapeTesselator is
// intentionally not built), plus the polygon->face builders used by conversions/meshes.py.
#include "compas.h"
#include "occt.h"

#include <utility>

#include <TopoDS.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Shell.hxx>
#include <TopExp_Explorer.hxx>
#include <TopAbs_ShapeEnum.hxx>
#include <TopAbs_Orientation.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <TopLoc_Location.hxx>
#include <gp_Trsf.hxx>
#include <BRep_Tool.hxx>
#include <BRep_Builder.hxx>
#include <BRepAdaptor_Curve.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <GCPnts_TangentialDeflection.hxx>
#include <Poly_Triangulation.hxx>
#include <Poly_Triangle.hxx>
#include <Poly_PolygonOnTriangulation.hxx>
#include <TColStd_Array1OfInteger.hxx>
#include <BRepBuilderAPI_MakePolygon.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepFill_Filling.hxx>
#include <GeomAbs_Shape.hxx>
#include <GeomAPI_PointsToBSpline.hxx>
#include <GeomFill.hxx>
#include <Geom_BSplineCurve.hxx>
#include <Geom_Surface.hxx>
#include <TColgp_Array1OfPnt.hxx>
#include <Precision.hxx>
#include <gp.hxx>

#include <cmath>

// Tessellate a shape -> (vertices (V,3) float64, triangles (T,3) int32, edge-polylines).
// Vertices/triangles are returned as zero-copy numpy arrays. Triangle winding is flipped for
// REVERSED faces so the mesh has consistent outward normals.
static nb::tuple tesselate(const Shape& s, double linear, double angular) {
    BRepMesh_IncrementalMesh mesher(s.shape, linear, Standard_False, angular, Standard_True);
    mesher.Perform();

    std::vector<double> verts;  // flat V*3
    std::vector<int> tris;      // flat T*3
    std::vector<std::vector<Triple>> edges;
    int nverts = 0;

    for (TopExp_Explorer ex(s.shape, TopAbs_FACE); ex.More(); ex.Next()) {
        TopoDS_Face face = TopoDS::Face(ex.Current());
        TopLoc_Location loc;
        opencascade::handle<Poly_Triangulation> tri = BRep_Tool::Triangulation(face, loc);
        if (tri.IsNull()) continue;

        const gp_Trsf trsf = loc.Transformation();
        const int offset = nverts;
        for (int i = 1; i <= tri->NbNodes(); ++i) {
            const gp_Pnt p = tri->Node(i).Transformed(trsf);
            verts.push_back(p.X());
            verts.push_back(p.Y());
            verts.push_back(p.Z());
            ++nverts;
        }

        const bool reversed = (face.Orientation() == TopAbs_REVERSED);
        for (int i = 1; i <= tri->NbTriangles(); ++i) {
            Standard_Integer n1, n2, n3;
            tri->Triangle(i).Get(n1, n2, n3);
            int a = offset + n1 - 1, b = offset + n2 - 1, c = offset + n3 - 1;
            if (reversed) std::swap(b, c);
            tris.push_back(a);
            tris.push_back(b);
            tris.push_back(c);
        }

        for (TopExp_Explorer ee(face, TopAbs_EDGE); ee.More(); ee.Next()) {
            opencascade::handle<Poly_PolygonOnTriangulation> pot =
                BRep_Tool::PolygonOnTriangulation(TopoDS::Edge(ee.Current()), tri, loc);
            if (pot.IsNull()) continue;
            std::vector<Triple> poly;
            const TColStd_Array1OfInteger& nodes = pot->Nodes();
            for (int i = nodes.Lower(); i <= nodes.Upper(); ++i) {
                const int g = (offset + nodes.Value(i) - 1) * 3;
                poly.push_back({verts[g], verts[g + 1], verts[g + 2]});
            }
            edges.push_back(poly);
        }
    }

    // Free edges (not part of any face) -- e.g. the wire produced by a section/slice -- have no
    // triangulation, so discretise their curves directly (cf. compas_occ's to_tesselation).
    TopTools_IndexedMapOfShape face_edges;
    for (TopExp_Explorer fx(s.shape, TopAbs_FACE); fx.More(); fx.Next())
        for (TopExp_Explorer ex(fx.Current(), TopAbs_EDGE); ex.More(); ex.Next())
            face_edges.Add(ex.Current());

    for (TopExp_Explorer ex(s.shape, TopAbs_EDGE); ex.More(); ex.Next()) {
        if (face_edges.Contains(ex.Current())) continue;
        BRepAdaptor_Curve curve(TopoDS::Edge(ex.Current()));
        GCPnts_TangentialDeflection discretizer(curve, angular, linear);
        std::vector<Triple> poly;
        for (int i = 1; i <= discretizer.NbPoints(); ++i) {
            const gp_Pnt p = discretizer.Value(i);
            poly.push_back({p.X(), p.Y(), p.Z()});
        }
        if (poly.size() >= 2) edges.push_back(poly);
    }

    const size_t V = static_cast<size_t>(nverts);
    const size_t T = tris.size() / 3;
    return nb::make_tuple(to_numpy(std::move(verts), {V, 3}), to_numpy(std::move(tris), {T, 3}), nb::cast(edges));
}

// Build a planar face from a closed polygon of coplanar points.
static Shape polygon_to_planar_face(const std::vector<Triple>& points) {
    BRepBuilderAPI_MakePolygon polygon;
    for (const auto& p : points) polygon.Add(to_pnt(p));
    polygon.Close();
    return Shape(BRepBuilderAPI_MakeFace(polygon.Wire()).Face());
}

// True if every point lies within `tol` of the polygon's own best-fit plane.
//
// The normal comes from Newell's method rather than a cross product of the first
// three points: Newell sums the contribution of every edge, so it stays
// well-conditioned on n-gons and on quads whose first three points happen to be
// nearly collinear - exactly the cases a naive cross product gets wrong.
//
// A degenerate polygon (zero-area, all points collinear) has no plane to fit and
// is reported as NOT planar, so it takes the surface-fitting fallback that has
// always handled it.
static bool polygon_is_planar(const std::vector<Triple>& points, double tol) {
    const size_t n = points.size();
    if (n < 4) return true;  // three points always span a plane

    double nx = 0.0, ny = 0.0, nz = 0.0;
    double cx = 0.0, cy = 0.0, cz = 0.0;
    for (size_t i = 0; i < n; ++i) {
        const Triple& a = points[i];
        const Triple& b = points[(i + 1) % n];
        nx += (a[1] - b[1]) * (a[2] + b[2]);
        ny += (a[2] - b[2]) * (a[0] + b[0]);
        nz += (a[0] - b[0]) * (a[1] + b[1]);
        cx += a[0];
        cy += a[1];
        cz += a[2];
    }

    const double mag = std::sqrt(nx * nx + ny * ny + nz * nz);
    if (mag <= gp::Resolution()) return false;  // degenerate: no plane to fit
    nx /= mag;
    ny /= mag;
    nz /= mag;
    cx /= static_cast<double>(n);
    cy /= static_cast<double>(n);
    cz /= static_cast<double>(n);

    for (const auto& p : points) {
        const double d = (p[0] - cx) * nx + (p[1] - cy) * ny + (p[2] - cz) * nz;
        if (std::abs(d) > tol) return false;
    }
    return true;
}

static Shape triangle_to_face(const std::vector<Triple>& points) {
    return polygon_to_planar_face(points);
}

// A flat quad is a plane, and building it as one is not just faster: a ruled
// surface through four coplanar points is reported as a BSpline by every
// downstream planarity test, which costs callers the cheap planar filters they
// would otherwise use. Only a genuinely twisted quad needs the ruled surface.
static Shape quad_to_face(const std::vector<Triple>& points, double tol) {
    if (polygon_is_planar(points, tol)) return polygon_to_planar_face(points);

    TColgp_Array1OfPnt a1(1, 2);
    a1.SetValue(1, to_pnt(points[0]));
    a1.SetValue(2, to_pnt(points[1]));
    TColgp_Array1OfPnt a2(1, 2);
    a2.SetValue(1, to_pnt(points[3]));
    a2.SetValue(2, to_pnt(points[2]));
    opencascade::handle<Geom_BSplineCurve> c1 = GeomAPI_PointsToBSpline(a1).Curve();
    opencascade::handle<Geom_BSplineCurve> c2 = GeomAPI_PointsToBSpline(a2).Curve();
    opencascade::handle<Geom_Surface> srf = GeomFill::Surface(c1, c2);
    return Shape(BRepBuilderAPI_MakeFace(srf, 1e-6).Face());
}

// Same reasoning as quad_to_face, and the saving is larger here: the fallback is
// BRepFill_Filling, an n-sided patch solve, where a flat n-gon only ever needed
// a wire on a plane.
static Shape ngon_to_face(const std::vector<Triple>& points, double tol) {
    if (polygon_is_planar(points, tol)) return polygon_to_planar_face(points);

    BRepBuilderAPI_MakePolygon polygon;
    for (const auto& p : points) polygon.Add(to_pnt(p));
    polygon.Build();
    polygon.Close();
    BRepFill_Filling nsided;
    for (TopExp_Explorer ex(polygon.Wire(), TopAbs_EDGE); ex.More(); ex.Next()) {
        nsided.Add(TopoDS::Edge(ex.Current()), GeomAbs_C0);
    }
    nsided.Build();
    return Shape(nsided.Face());
}

void register_meshing(nb::module_& m) {
    // NOTE: do NOT add a blanket nb::gil_scoped_release here -- tesselate builds the nb::ndarray
    // / nb::tuple return value inside its body, which requires the GIL. (Releasing it only around
    // the internal BRepMesh call would need manual scoping inside tesselate.)
    m.def("tesselate", &tesselate);
    m.def("triangle_to_face", &triangle_to_face);
    // `tol` is the distance below which the input counts as flat and a planar
    // face is built instead of a fitted surface. Precision::Confusion() is
    // OCCT's own "these points are the same point" threshold, so anything
    // within it was never distinguishable from planar in the first place.
    m.def("quad_to_face", &quad_to_face, nb::arg("points"), nb::arg("tol") = Precision::Confusion());
    m.def("ngon_to_face", &ngon_to_face, nb::arg("points"), nb::arg("tol") = Precision::Confusion());
    // shell_from_faces is registered by register_make (brep_make.cpp).
}
