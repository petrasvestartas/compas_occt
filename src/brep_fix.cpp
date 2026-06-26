// brep_fix.cpp - healing / fixing / simplification free functions (sew, fix_shell,
// solid_from_shell, fix_face, fix_wire, simplify, shape_reversed).
#include "compas.h"
#include "occt.h"

#include <TopoDS.hxx>
#include <TopoDS_Shape.hxx>
#include <TopoDS_Shell.hxx>
#include <TopoDS_Solid.hxx>
#include <BRepBuilderAPI_Sewing.hxx>
#include <ShapeFix_Shell.hxx>
#include <ShapeFix_Solid.hxx>
#include <ShapeFix_Face.hxx>
#include <ShapeFix_Wire.hxx>
#include <ShapeUpgrade_UnifySameDomain.hxx>

static Shape shape_sew(const Shape& s) {
    BRepBuilderAPI_Sewing sewer;
    sewer.Load(s.shape);
    sewer.Perform();
    return Shape(sewer.SewedShape());
}

static Shape fix_shell(const Shape& s) {
    ShapeFix_Shell fixer(TopoDS::Shell(s.shape));
    fixer.Perform();
    return Shape(fixer.Shell());
}

static Shape solid_from_shell(const Shape& s) {
    ShapeFix_Solid fixer;
    return Shape(fixer.SolidFromShell(TopoDS::Shell(s.shape)));
}

static Shape fix_face(const Shape& s) {
    ShapeFix_Face fixer(TopoDS::Face(s.shape));
    fixer.Perform();
    return Shape(fixer.Face());
}

static Shape fix_wire(const Shape& s) {
    ShapeFix_Wire fixer;
    fixer.Load(TopoDS::Wire(s.shape));
    fixer.Perform();
    return Shape(fixer.Wire());
}

static Shape simplify(const Shape& s, bool merge_edges, bool merge_faces, double lineardeflection, double angulardeflection) {
    ShapeUpgrade_UnifySameDomain simplifier;
    simplifier.SetLinearTolerance(lineardeflection);
    simplifier.SetAngularTolerance(angulardeflection);
    simplifier.Initialize(s.shape, merge_edges, merge_faces);
    simplifier.Build();
    return Shape(simplifier.Shape());
}

static Shape shape_reversed(const Shape& s) {
    TopoDS_Shape r = s.shape;
    r.Reverse();
    return Shape(r);
}

void register_fix(nb::module_& m) {
    m.def("sew", &shape_sew);
    m.def("fix_shell", &fix_shell);
    m.def("solid_from_shell", &solid_from_shell);
    m.def("fix_face", &fix_face);
    m.def("fix_wire", &fix_wire);
    m.def("simplify", &simplify);
    m.def("shape_reversed", &shape_reversed);
}
