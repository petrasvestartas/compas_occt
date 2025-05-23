#include "compas.h"
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/unique_ptr.h>
#include <nanobind/stl/vector.h>
#include <TColgp_Array2OfPnt.hxx>
#include <TColStd_Array2OfReal.hxx>
#include <TColStd_Array1OfReal.hxx>
#include <TColStd_Array1OfInteger.hxx>
#include <Geom_BSplineSurface.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <TopoDS_Face.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <BRep_Tool.hxx>
#include <TopLoc_Location.hxx>
#include <Poly_Triangulation.hxx>

// For timing measurements
#include <chrono>
#include <iostream>

// For parallel processing
#include <thread>
#include <vector>
#include <mutex>
#include <algorithm>
#include <functional>

struct NB_Geom_BSplineSurface {
    Handle(Geom_BSplineSurface) surface;
    NB_Geom_BSplineSurface(Handle(Geom_BSplineSurface) surface) : surface(surface) {}
};

std::unique_ptr<NB_Geom_BSplineSurface> create_nurbs_surface_from_points(
    const nb::ndarray<double, nb::numpy>& points, 
    int rows, int cols,
    int degree_u = 3, 
    int degree_v = 3) {
    
    // Validate dimensions
    if (rows < 2 || cols < 2) {
        throw std::runtime_error("Grid dimensions must be at least 2x2");
    }
    
    if (points.size() != rows * cols * 3) {
        throw std::runtime_error("Points array size does not match grid dimensions");
    }
    
    // Adjust degrees if needed (must be less than number of points)
    if (cols <= degree_u) {
        degree_u = cols - 1;
    }
    
    if (rows <= degree_v) {
        degree_v = rows - 1;
    }
    
    // Calculate orders (degree + 1)
    int u_order = degree_u + 1;
    int v_order = degree_v + 1;
    
    // Create poles array
    TColgp_Array2OfPnt poles(1, rows, 1, cols);
    TColStd_Array2OfReal weights(1, rows, 1, cols);
    
    // Fill in poles and weights
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            int idx = i * cols + j;
            poles.SetValue(i+1, j+1, gp_Pnt(
                points.data()[idx*3],
                points.data()[idx*3+1],
                points.data()[idx*3+2]));
            weights.SetValue(i+1, j+1, 1.0); // All weights 1.0
        }
    }
    
    // Create knots and multiplicities for U direction
    int x_u = cols - u_order;
    TColStd_Array1OfReal knots_u(1, 2 + x_u);
    TColStd_Array1OfInteger mults_u(1, 2 + x_u);
    
    // First knot with multiplicity = u_order
    knots_u.SetValue(1, 0.0);
    mults_u.SetValue(1, u_order);
    
    // Middle knots with multiplicity = 1
    for (int i = 0; i < x_u; i++) {
        knots_u.SetValue(i + 2, float(i + 1));
        mults_u.SetValue(i + 2, 1);
    }
    
    // Last knot with multiplicity = u_order
    knots_u.SetValue(2 + x_u, float(1 + x_u));
    mults_u.SetValue(2 + x_u, u_order);
    
    // Create knots and multiplicities for V direction
    int x_v = rows - v_order;
    TColStd_Array1OfReal knots_v(1, 2 + x_v);
    TColStd_Array1OfInteger mults_v(1, 2 + x_v);
    
    // First knot with multiplicity = v_order
    knots_v.SetValue(1, 0.0);
    mults_v.SetValue(1, v_order);
    
    // Middle knots with multiplicity = 1
    for (int i = 0; i < x_v; i++) {
        knots_v.SetValue(i + 2, float(i + 1));
        mults_v.SetValue(i + 2, 1);
    }
    
    // Last knot with multiplicity = v_order
    knots_v.SetValue(2 + x_v, float(1 + x_v));
    mults_v.SetValue(2 + x_v, v_order);
    
    // Create the BSpline surface
    Handle(Geom_BSplineSurface) surface = new Geom_BSplineSurface(
        poles, weights, knots_u, knots_v, 
        mults_u, mults_v, degree_u, degree_v,
        Standard_False, Standard_False  // Not periodic
    );
    
    // Return as a unique_ptr to NB_Geom_BSplineSurface
    return std::make_unique<NB_Geom_BSplineSurface>(surface);
}

Eigen::Matrix<double, Eigen::Dynamic, 3, Eigen::RowMajor> get_control_points(const NB_Geom_BSplineSurface& nurbs_surface) {
    const Handle(Geom_BSplineSurface)& surface = nurbs_surface.surface;
    int rows = surface->NbUPoles();
    int cols = surface->NbVPoles();
    
    Eigen::Matrix<double, Eigen::Dynamic, 3, Eigen::RowMajor> points(rows * cols, 3);
    
    for (int i = 1; i <= rows; i++) {
        for (int j = 1; j <= cols; j++) {
            gp_Pnt p = surface->Pole(i, j);
            int idx = (i-1) * cols + (j-1);
            
            points(idx, 0) = p.X();
            points(idx, 1) = p.Y();
            points(idx, 2) = p.Z();
        }
    }
    
    return points;
}

// 4. Get isocurves on the surface as polylines
std::vector<Eigen::Matrix<double, Eigen::Dynamic, 3, Eigen::RowMajor>> get_isocurves(
    const NB_Geom_BSplineSurface& nurbs_surface,
    bool u_direction,
    int divisions,
    int points_per_curve=50) {
    const Handle(Geom_BSplineSurface)& surface = nurbs_surface.surface;
    
    // Get the parameter range
    double u_min, u_max, v_min, v_max;
    surface->Bounds(u_min, u_max, v_min, v_max);
    
    // Create vector to hold polylines
    std::vector<Eigen::Matrix<double, Eigen::Dynamic, 3, Eigen::RowMajor>> isocurves;
    
    if (u_direction) {
        // Create isocurves at constant v (horizontal curves)
        for (int i = 0; i < divisions+1; i++) {
            // Calculate v parameter
            double v = v_min + (v_max - v_min) * static_cast<double>(i) / divisions;
            
            // Create a polyline with points along the curve
            Eigen::Matrix<double, Eigen::Dynamic, 3, Eigen::RowMajor> curve_points(points_per_curve, 3);
            
            for (int j = 0; j < points_per_curve; j++) {
                double u = u_min + (u_max - u_min) * static_cast<double>(j) / (points_per_curve - 1);
                gp_Pnt point = surface->Value(u, v);
                
                curve_points(j, 0) = point.X();
                curve_points(j, 1) = point.Y();
                curve_points(j, 2) = point.Z();
            }
            
            isocurves.push_back(curve_points);
        }
    } else {
        // Create isocurves at constant u (vertical curves)
        for (int i = 0; i <= divisions; i++) {
            // Calculate u parameter
            double u = u_min + (u_max - u_min) * static_cast<double>(i) / divisions;
            
            // Create a polyline with points along the curve
            Eigen::Matrix<double, Eigen::Dynamic, 3, Eigen::RowMajor> curve_points(points_per_curve, 3);
            
            for (int j = 0; j < points_per_curve; j++) {
                double v = v_min + (v_max - v_min) * static_cast<double>(j) / (points_per_curve - 1);
                gp_Pnt point = surface->Value(u, v);
                
                curve_points(j, 0) = point.X();
                curve_points(j, 1) = point.Y();
                curve_points(j, 2) = point.Z();
            }
            
            isocurves.push_back(curve_points);
        }
    }
    
    return isocurves;
}

// Original function for backward compatibility
std::tuple<Eigen::Matrix<double, Eigen::Dynamic, 3, Eigen::RowMajor>, 
          Eigen::Matrix<int, Eigen::Dynamic, 3, Eigen::RowMajor>> get_mesh(
    const NB_Geom_BSplineSurface& nurbs_surface, 
    double deflection = 0.001) {
    
    const Handle(Geom_BSplineSurface)& surface = nurbs_surface.surface;
    
    // Create a topological face from the surface
    TopoDS_Face face = BRepBuilderAPI_MakeFace(surface, 1e-6);
    BRepMesh_IncrementalMesh mesh(face, deflection);
    TopLoc_Location loc;
    Handle(Poly_Triangulation) triangulation = BRep_Tool::Triangulation(face, loc);
    
    Eigen::Matrix<double, Eigen::Dynamic, 3, Eigen::RowMajor> vertices(triangulation->NbNodes(), 3);
    double* vertices_data = vertices.data();
    for (int i = 1; i <= triangulation->NbNodes(); i++) {
        gp_Pnt p = triangulation->InternalNodes().Value(i-1).Transformed(loc);
        *vertices_data++ = p.X();
        *vertices_data++ = p.Y();
        *vertices_data++ = p.Z();
    }
    
    Eigen::Matrix<int, Eigen::Dynamic, 3, Eigen::RowMajor> triangles(triangulation->NbTriangles(), 3);
    int* triangles_data = triangles.data();
    for (int i = 1; i <= triangulation->NbTriangles(); i++) {
        int n1, n2, n3;
        triangulation->InternalTriangles().Value(i).Get(n1, n2, n3);
        *triangles_data++ = n1 - 1;
        *triangles_data++ = n2 - 1;
        *triangles_data++ = n3 - 1;
    }
    
    return std::make_tuple(std::move(vertices), std::move(triangles));
}

NB_MODULE(_nurbssurface, m) {
    m.doc() = "OCCT NURBS surface functions";
    
    nb::class_<NB_Geom_BSplineSurface>(m, "BSplineSurface");
    
    m.def("create_nurbs_surface_from_points", 
        &create_nurbs_surface_from_points,
        nb::arg("points"), 
        nb::arg("rows"),
        nb::arg("cols"),
        nb::arg("degree_u") = 3, 
        nb::arg("degree_v") = 3);
    
    m.def("get_control_points", 
        &get_control_points,
        nb::arg("surface"));
    
    m.def("get_mesh", 
        &get_mesh,
        nb::arg("surface"), 
        nb::arg("deflection") = 0.01,
        "Triangulate a NURBS surface into a mesh with vertices and faces");
    
    m.def("get_isocurves",
        &get_isocurves,
        nb::arg("surface"),
        nb::arg("u_direction"),
        nb::arg("divisions"),
        nb::arg("points_per_curve") = 50,
        "Extract isocurves from a NURBS surface in U or V direction");
}