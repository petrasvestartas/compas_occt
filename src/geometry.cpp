#include "compas.h"
#include <nanobind/stl/array.h>
#include <nanobind/stl/unique_ptr.h>
#include <gp_Pnt.hxx>
#include <Precision.hxx>
#include <memory>

// =============================================================================
// Conversion Functions
// =============================================================================

std::unique_ptr<gp_Pnt, nb::deleter<gp_Pnt>> gp_Pnt_init(double x, double y, double z) {
    return std::unique_ptr<gp_Pnt, nb::deleter<gp_Pnt>>(
        new gp_Pnt(x, y, z), 
        nb::deleter<gp_Pnt>{}
    );
}

// =============================================================================
// Nanobind Module
// =============================================================================

NB_MODULE(_geometry, m) {
    m.doc() = "COMPAS OCCT geometry conversion functions";
    
    // Bind the gp_Pnt class (methods only, no constructor)
    nb::class_<gp_Pnt>(m, "gp_Pnt")
        .def("X", &gp_Pnt::X)
        .def("Y", &gp_Pnt::Y)
        .def("Z", &gp_Pnt::Z)
        .def("SetX", &gp_Pnt::SetX)
        .def("SetY", &gp_Pnt::SetY)
        .def("SetZ", &gp_Pnt::SetZ)
        .def("SetCoord", nb::overload_cast<const Standard_Real, const Standard_Real, const Standard_Real>(&gp_Pnt::SetCoord))
        .def("Coord", [](const gp_Pnt& self) {
            Standard_Real x, y, z;
            self.Coord(x, y, z);
            return std::array<Standard_Real, 3>{x, y, z};
        })
        .def("Distance", &gp_Pnt::Distance)
        .def("SquareDistance", &gp_Pnt::SquareDistance)
        .def("IsEqual", &gp_Pnt::IsEqual)
        .def("__eq__", [](const gp_Pnt& self, const gp_Pnt& other) {
            return self.IsEqual(other, Precision::Confusion());
        })
        .def("__repr__", [](const gp_Pnt& self) {
            return "gp_Pnt(" + std::to_string(self.X()) + ", " + 
                   std::to_string(self.Y()) + ", " + std::to_string(self.Z()) + ")";
        });
    
    // Zero-copy unique pointer version (primary function)
    m.def("gp_Pnt_init", &gp_Pnt_init, 
          "x"_a, "y"_a, "z"_a,
          "Convert coordinates to an OCC gp_Pnt unique_ptr (zero-copy)");
}