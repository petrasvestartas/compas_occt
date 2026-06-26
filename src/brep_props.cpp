// brep_props.cpp - geometric/topological property free functions backing OCCBrep
// (area/volume/centroid/length/aabb/obb/location/is_*).
#include "compas.h"
#include "occt.h"

#include <utility>
#include <tuple>

#include <TopoDS.hxx>
#include <TopLoc_Location.hxx>
#include <gp_Trsf.hxx>
#include <GProp_GProps.hxx>
#include <BRepGProp.hxx>
#include <Bnd_Box.hxx>
#include <Bnd_OBB.hxx>
#include <BRepBndLib.hxx>
#include <BRepAlgo.hxx>

static double brep_area(const Shape& s) {
    GProp_GProps props;
    BRepGProp::SurfaceProperties(s.shape, props);
    return props.Mass();
}

static double brep_volume(const Shape& s) {
    GProp_GProps props;
    BRepGProp::VolumeProperties(s.shape, props);
    return props.Mass();
}

static Triple brep_centroid(const Shape& s) {
    GProp_GProps props;
    BRepGProp::VolumeProperties(s.shape, props);
    return from_pnt(props.CentreOfMass());
}

static double edge_length(const Shape& s) {
    GProp_GProps props;
    BRepGProp::LinearProperties(s.shape, props);
    return props.Mass();
}

// (cornermin, cornermax)
static std::pair<Triple, Triple> brep_aabb(const Shape& s, bool optimal) {
    Bnd_Box box;
    if (optimal)
        BRepBndLib::AddOptimal(s.shape, box);
    else
        BRepBndLib::Add(s.shape, box, Standard_True);
    return {from_pnt(box.CornerMin()), from_pnt(box.CornerMax())};
}

// (frame, xhsize, yhsize, zhsize); frame = (point, xaxis, yaxis)
static std::tuple<Ax, double, double, double> brep_obb(const Shape& s) {
    Bnd_OBB box;
    BRepBndLib::AddOBB(s.shape, box, Standard_True, Standard_True, Standard_True);
    const gp_Ax3 ax3 = box.Position();
    Ax frame{from_pnt(ax3.Location()), from_dir(ax3.XDirection()), from_dir(ax3.YDirection())};
    return {frame, box.XHSize(), box.YHSize(), box.ZHSize()};
}

// 3x4 row-major matrix of the shape's location transformation (Python wraps to 4x4).
static std::array<std::array<double, 4>, 3> location_frame(const Shape& s) {
    gp_Trsf t = s.shape.Location().Transformation();
    std::array<std::array<double, 4>, 3> m{};
    for (int i = 1; i <= 3; ++i)
        for (int j = 1; j <= 4; ++j)
            m[i - 1][j - 1] = t.Value(i, j);
    return m;
}

static bool brep_is_valid(const Shape& s) { return BRepAlgo::IsValid(s.shape); }
static bool brep_is_closed(const Shape& s) { return s.shape.Closed(); }
static bool brep_is_infinite(const Shape& s) { return s.shape.Infinite(); }
static bool brep_is_convex(const Shape& s) { return s.shape.Convex(); }
static bool brep_is_orientable(const Shape& s) { return s.shape.Orientable(); }

void register_props(nb::module_& m) {
    m.def("area", &brep_area);
    m.def("volume", &brep_volume);
    m.def("centroid", &brep_centroid);
    m.def("edge_length", &edge_length);
    m.def("aabb", &brep_aabb);
    m.def("obb", &brep_obb);
    m.def("location_frame", &location_frame);
    m.def("is_valid", &brep_is_valid);
    m.def("is_closed", &brep_is_closed);
    m.def("is_infinite", &brep_is_infinite);
    m.def("is_convex", &brep_is_convex);
    m.def("is_orientable", &brep_is_orientable);
}
