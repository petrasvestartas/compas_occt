// occt.h - shared C++ helpers for converting between plain data (crossing the nanobind
// boundary) and OCCT gp_* primitives. These gp_* types are NEVER exposed to Python; they
// are built/consumed entirely inside C++ free functions.
#pragma once

#include "compas.h"
#include "handles.h"

#include <array>
#include <vector>
#include <initializer_list>
#include <nanobind/ndarray.h>

#include <gp_Pnt.hxx>
#include <gp_Vec.hxx>
#include <gp_Dir.hxx>
#include <gp_Pnt2d.hxx>
#include <gp_Vec2d.hxx>
#include <gp_Dir2d.hxx>
#include <gp_Ax1.hxx>
#include <gp_Ax2.hxx>
#include <gp_Ax3.hxx>
#include <gp_Ax2d.hxx>
#include <gp_Ax22d.hxx>
#include <gp_Trsf.hxx>

using Triple = std::array<double, 3>;
using Pair = std::array<double, 2>;

// Zero-copy hand-off: move a std::vector to the heap and expose its buffer to Python as a
// numpy array that owns (and frees) it. No element copy crosses the boundary.
template <typename T>
inline nb::ndarray<nb::numpy, T> to_numpy(std::vector<T>&& v, std::initializer_list<size_t> shape) {
    auto* held = new std::vector<T>(std::move(v));
    nb::capsule owner(held, [](void* p) noexcept { delete static_cast<std::vector<T>*>(p); });
    return nb::ndarray<nb::numpy, T>(held->data(), shape, owner);
}

// ---------------------------------------------------------------------------
// plain data -> OCCT
// ---------------------------------------------------------------------------

inline gp_Pnt to_pnt(const Triple& p) { return gp_Pnt(p[0], p[1], p[2]); }
inline gp_Vec to_vec(const Triple& v) { return gp_Vec(v[0], v[1], v[2]); }
inline gp_Dir to_dir(const Triple& v) { return gp_Dir(v[0], v[1], v[2]); }
inline gp_Pnt2d to_pnt2d(const Triple& p) { return gp_Pnt2d(p[0], p[1]); }
inline gp_Vec2d to_vec2d(const Triple& v) { return gp_Vec2d(v[0], v[1]); }
inline gp_Dir2d to_dir2d(const Triple& v) { return gp_Dir2d(v[0], v[1]); }

// A COMPAS plane is (point, normal). OCCT gp_Ax2/Ax3 want (location, N-direction, Vx-direction).
// For a plane we only have the normal, so let OCCT pick an arbitrary in-plane X.
inline gp_Ax2 to_ax2(const Triple& point, const Triple& normal) {
    return gp_Ax2(to_pnt(point), to_dir(normal));
}
inline gp_Ax3 to_ax3(const Triple& point, const Triple& normal) {
    return gp_Ax3(to_pnt(point), to_dir(normal));
}
// A COMPAS frame is (point, xaxis, yaxis); zaxis = xaxis x yaxis. OCCT Ax2/Ax3 take
// (location, N=zaxis, Vx=xaxis).
inline gp_Ax2 frame_to_ax2(const Triple& point, const Triple& xaxis, const Triple& zaxis) {
    return gp_Ax2(to_pnt(point), to_dir(zaxis), to_dir(xaxis));
}
inline gp_Ax3 frame_to_ax3(const Triple& point, const Triple& xaxis, const Triple& zaxis) {
    return gp_Ax3(to_pnt(point), to_dir(zaxis), to_dir(xaxis));
}
inline gp_Ax22d frame_to_ax22d(const Triple& point, const Triple& xaxis, const Triple& yaxis) {
    return gp_Ax22d(to_pnt2d(point), to_dir2d(xaxis), to_dir2d(yaxis));
}

// A COMPAS Transformation row-major list[:12] -> gp_Trsf.
inline gp_Trsf to_trsf(const std::array<double, 12>& m) {
    gp_Trsf trsf;
    trsf.SetValues(m[0], m[1], m[2], m[3],
                   m[4], m[5], m[6], m[7],
                   m[8], m[9], m[10], m[11]);
    return trsf;
}

// ---------------------------------------------------------------------------
// OCCT -> plain data
// ---------------------------------------------------------------------------

inline Triple from_pnt(const gp_Pnt& p) { return {p.X(), p.Y(), p.Z()}; }
inline Triple from_vec(const gp_Vec& v) { return {v.X(), v.Y(), v.Z()}; }
inline Triple from_dir(const gp_Dir& d) { return {d.X(), d.Y(), d.Z()}; }
inline Triple from_pnt2d(const gp_Pnt2d& p) { return {p.X(), p.Y(), 0.0}; }
inline Triple from_dir2d(const gp_Dir2d& d) { return {d.X(), d.Y(), 0.0}; }

inline std::vector<Triple> from_pnts(const std::vector<gp_Pnt>& pnts) {
    std::vector<Triple> out;
    out.reserve(pnts.size());
    for (const auto& p : pnts) out.push_back(from_pnt(p));
    return out;
}

// ---------------------------------------------------------------------------
// frame plain data <-> gp_Ax2 / gp_Ax3
// ---------------------------------------------------------------------------
//
// A COMPAS frame crosses the boundary as Ax = (point, xaxis, yaxis), exactly the layout
// produced by conversions.frame_to_occ_ax2 / frame_to_occ_ax3. OCCT's gp_Ax2/gp_Ax3 want
// (location, N = zaxis, Vx = xaxis), so we reconstruct the zaxis as xaxis x yaxis here.

using Ax = std::array<Triple, 3>;  // (point, xaxis, yaxis)

inline gp_Ax2 to_ax2_from_frame(const Ax& f) {
    gp_Dir x = to_dir(f[1]);
    gp_Dir y = to_dir(f[2]);
    gp_Vec z = gp_Vec(x).Crossed(gp_Vec(y));
    return gp_Ax2(to_pnt(f[0]), gp_Dir(z), x);
}
inline gp_Ax3 to_ax3_from_frame(const Ax& f) {
    gp_Dir x = to_dir(f[1]);
    gp_Dir y = to_dir(f[2]);
    gp_Vec z = gp_Vec(x).Crossed(gp_Vec(y));
    return gp_Ax3(to_pnt(f[0]), gp_Dir(z), x);
}
inline Ax from_ax2(const gp_Ax2& a) {
    return {from_pnt(a.Location()), from_dir(a.XDirection()), from_dir(a.YDirection())};
}
inline Ax from_ax3(const gp_Ax3& a) {
    return {from_pnt(a.Location()), from_dir(a.XDirection()), from_dir(a.YDirection())};
}
