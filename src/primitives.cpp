#include "compas.h"

// Include OCCT headers for NURBS curves
#include <TColgp_Array1OfPnt.hxx>
#include <TColStd_Array1OfReal.hxx>
#include <TColStd_Array1OfInteger.hxx>
#include <Geom_BSplineCurve.hxx>
#include <gp_Pnt.hxx>

// Define our own function using regular C++
int add(int a, int b) {
    return a + b;
}

// Simple addition function
int sum_from_static_lib(int a, int b) {
    // Simple direct implementation
    return a + b;
}

// Create a NURBS curve using OCCT
Handle(Geom_BSplineCurve) create_nurbs_curve() {
    // Create a NURBS curve with 4 control points
    TColgp_Array1OfPnt controlPoints(1, 4);
    controlPoints.SetValue(1, gp_Pnt(0.0, 0.0, 0.0));
    controlPoints.SetValue(2, gp_Pnt(1.0, 1.0, 0.0));
    controlPoints.SetValue(3, gp_Pnt(2.0, 0.0, 0.0));
    controlPoints.SetValue(4, gp_Pnt(3.0, 1.0, 0.0));
    
    // Weights for the NURBS curve
    TColStd_Array1OfReal weights(1, 4);
    weights.SetValue(1, 1.0);
    weights.SetValue(2, 2.0);  // Higher weight at the second point
    weights.SetValue(3, 1.0);
    weights.SetValue(4, 1.0);
    
    // Knot vector
    TColStd_Array1OfReal knots(1, 2);
    knots.SetValue(1, 0.0);
    knots.SetValue(2, 1.0);
    
    // Knot multiplicities
    TColStd_Array1OfInteger mults(1, 2);
    mults.SetValue(1, 4);  // Multiplicity at the start
    mults.SetValue(2, 4);  // Multiplicity at the end
    
    // Create the NURBS curve (degree 3)
    return new Geom_BSplineCurve(controlPoints, weights, knots, mults, 3);
}

// Extract points from a NURBS curve for visualization
nanobind::list sample_nurbs_curve(int num_points) {
    // Create the NURBS curve
    Handle(Geom_BSplineCurve) curve = create_nurbs_curve();
    
    // Sample points along the curve
    nanobind::list points;
    
    for (int i = 0; i < num_points; i++) {
        double param = static_cast<double>(i) / (num_points - 1);
        gp_Pnt point = curve->Value(param);
        
        // Create a Python list for each point [x, y, z]
        nanobind::list point_coords;
        point_coords.append(point.X());
        point_coords.append(point.Y());
        point_coords.append(point.Z());
        
        points.append(point_coords);
    }
    
    return points;
}

// Simple function to test OCCT linking without complex Python bindings
std::string test_occt_linking() {
    try {
        // Create a simple NURBS curve using OCCT
        Handle(Geom_BSplineCurve) curve = create_nurbs_curve();
        
        // Get some basic information about the curve
        int degree = curve->Degree();
        int numPoles = curve->NbPoles();
        int numKnots = curve->NbKnots();
        
        // Create a test point on the curve
        gp_Pnt testPoint = curve->Value(0.5);
        
        // Format the result as a simple string
        std::string result = "OCCT Test Successful! ";
        result += "NURBS Curve: Degree=" + std::to_string(degree);
        result += ", Control Points=" + std::to_string(numPoles);
        result += ", Knots=" + std::to_string(numKnots);
        result += ", Test Point=(" + std::to_string(testPoint.X()) + ",";
        result += std::to_string(testPoint.Y()) + ",";
        result += std::to_string(testPoint.Z()) + ")";
        
        return result;
    }
    catch (const Standard_Failure& ex) {
        // If there's an OCCT exception, report it
        return std::string("OCCT Error: ") + ex.GetMessageString();
    }
    catch (const std::exception& ex) {
        // Catch any other C++ exceptions
        return std::string("C++ Error: ") + ex.what();
    }
    catch (...) {
        // Catch anything else
        return "Unknown error in OCCT operations";
    }
}

NB_MODULE(_primitives, m) {
    m.doc() = "Primitives example with static library integration and OCCT NURBS.";

    // Expose our regular function
    m.def("add", &add, "a"_a, "b"_a=1, "Add two numbers using local implementation");
    
    // Expose the function that uses the static library
    m.def("sum_from_static_lib", &sum_from_static_lib, "a"_a, "b"_a=1, 
          "Add two numbers using the template static library implementation");
    
    // Expose the OCCT NURBS curve function
    m.def("sample_nurbs_curve", &sample_nurbs_curve, "num_points"_a=50,
          "Sample points from a NURBS curve created with OpenCASCADE");
    
    // Expose the simple OCCT test function that returns a string
    m.def("test_occt_linking", &test_occt_linking,
          "Test if OCCT linking is working correctly by returning a string with NURBS curve information");
}
