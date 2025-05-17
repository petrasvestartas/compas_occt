#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>

#include <iostream>
#include <TColgp_Array1OfPnt.hxx>
#include <TColStd_Array1OfReal.hxx>
#include <TColStd_Array1OfInteger.hxx>
#include <Geom_BSplineCurve.hxx>
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <TopoDS_Edge.hxx>
#include <BRepTools.hxx>
#include <Standard_Version.hxx>

namespace nb = nanobind;

// Test function to verify OCCT is properly linked
std::string test_occt_nurbs() {
    std::stringstream output;
    output << "OCCT NURBS Curve Example" << std::endl;
    output << "Using Open CASCADE Technology version: " 
           << OCC_VERSION_STRING_EXT << std::endl;
    
    // Step 1: Define control points for the NURBS curve
    const int numPoles = 6;
    TColgp_Array1OfPnt poles(1, numPoles);
    
    // Create a sinusoidal wave shape with the control points
    poles(1) = gp_Pnt(0, 0, 0);
    poles(2) = gp_Pnt(10, 20, 0);
    poles(3) = gp_Pnt(20, -10, 0);
    poles(4) = gp_Pnt(30, 20, 0);
    poles(5) = gp_Pnt(40, -10, 0);
    poles(6) = gp_Pnt(50, 0, 0);
    
    // Step 2: Define weights for the NURBS curve
    // Non-uniform weights make this a true NURBS curve as opposed to a B-spline curve
    TColStd_Array1OfReal weights(1, numPoles);
    weights(1) = 1.0;
    weights(2) = 2.0; // Higher weight means the curve is pulled more toward this point
    weights(3) = 0.8;
    weights(4) = 2.0;
    weights(5) = 0.8;
    weights(6) = 1.0;
    
    // Step 3: Define knots and multiplicities
    // For a cubic (degree 3) curve with 6 control points, we need 6 + 3 + 1 = 10 knots
    // But we'll use a clamped knot vector with multiplicity 4 at the ends, leading to 6 knot values
    TColStd_Array1OfReal knots(1, 4);
    knots(1) = 0.0;
    knots(2) = 0.25;
    knots(3) = 0.75;
    knots(4) = 1.0;
    
    TColStd_Array1OfInteger mults(1, 4);
    mults(1) = 4; // Multiplicity 4 at the start (curve passes through first control point)
    mults(2) = 1;
    mults(3) = 1;
    mults(4) = 4; // Multiplicity 4 at the end (curve passes through last control point)
    
    // Step 4: Create the NURBS curve
    // Degree 3 (cubic)
    Handle(Geom_BSplineCurve) nurbsCurve = new Geom_BSplineCurve(
        poles, weights, knots, mults, 3, false); // false = non-periodic curve
    
    // Print curve information
    output << "NURBS curve created with:" << std::endl;
    output << "- Number of control points: " << nurbsCurve->NbPoles() << std::endl;
    output << "- Degree: " << nurbsCurve->Degree() << std::endl;
    output << "- Number of knots: " << nurbsCurve->NbKnots() << std::endl;
    output << "- Is rational: " << (nurbsCurve->IsRational() ? "Yes" : "No") << std::endl;
    
    // Create topological edge from the curve
    TopoDS_Edge edge = BRepBuilderAPI_MakeEdge(nurbsCurve);
    
    // Save the edge to BREP file
    BRepTools::Write(edge, "nurbs_curve.brep");
    
    output << "NURBS curve created successfully!" << std::endl;
    output << "Result saved as nurbs_curve.brep" << std::endl;
    
    return output.str();
}

NB_MODULE(_curves, m) {
    m.doc() = "OCCT curve testing module";
    
    m.def("test_occt_nurbs", &test_occt_nurbs, "Test OCCT NURBS curve creation");
    
    // Get OCCT version
    m.def("get_occt_version", []() { 
        return std::string(OCC_VERSION_STRING_EXT); 
    }, "Return the OCCT version");
}
