// geometry.cpp - the `_geometry` extension module.
//
// Most COMPAS<->OCC conversions are pure Python in compas_occt (see conversions/*.py),
// because they only shuffle plain numbers. Only the conversions that genuinely need OCCT
// live here - currently extracting the 3x4 transformation matrix out of a TopLoc_Location
// (used by conversions.location_to_compas).
#include "compas.h"
#include "occt.h"

#include <TopLoc_Location.hxx>
#include <gp_Trsf.hxx>

// Return the row-major 3x4 affine matrix of a shape location's transformation.
// Python wraps this into a 4x4 and builds a compas Frame.
std::array<std::array<double, 4>, 3> trsf_to_matrix(const gp_Trsf& t) {
    std::array<std::array<double, 4>, 3> m{};
    for (int i = 1; i <= 3; ++i)
        for (int j = 1; j <= 4; ++j)
            m[i - 1][j - 1] = t.Value(i, j);
    return m;
}

void register_geometry(nb::module_& m) {
    m.def("matrix_from_values", [](const std::array<double, 12>& values) { return trsf_to_matrix(to_trsf(values)); }, "values"_a);
}
