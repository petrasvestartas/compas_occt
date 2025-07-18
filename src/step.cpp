#include "compas.h"
#include <nanobind/stl/string.h>

// STEP I/O includes
#include <STEPControl_Reader.hxx>
#include <STEPControl_Writer.hxx>
#include <TopoDS_Shape.hxx>
#include <IFSelect_ReturnStatus.hxx>

// Transformation includes
#include <gp_Trsf.hxx>
#include <gp_Vec.hxx>
#include <BRepBuilderAPI_Transform.hxx>
#include <TopoDS_Compound.hxx>
#include <BRep_Builder.hxx>

void translate_step() {
  // Read original STEP file
  STEPControl_Reader reader;
  IFSelect_ReturnStatus status = reader.ReadFile("/home/pv/brg/code/compas_occt/data/screw.step");
  if (status != IFSelect_RetDone) return;
  
  reader.TransferRoots();
  TopoDS_Shape original = reader.Shape(1);
  if (original.IsNull()) return;
  
  // Create compound to hold all translated shapes
  TopoDS_Compound compound;
  BRep_Builder builder;
  builder.MakeCompound(compound);
  
  // Create 4 translated copies
  double positions[4][3] = {{0, 0, 0}, {10, 0, 0}, {0, 10, 0}, {10, 10, 0}};
  
  for (int i = 0; i < 4; i++) {
    gp_Trsf transform;
    transform.SetTranslation(gp_Vec(positions[i][0], positions[i][1], positions[i][2]));
    
    BRepBuilderAPI_Transform transformer(original, transform);
    TopoDS_Shape translated = transformer.Shape();
    
    builder.Add(compound, translated);
  }
  
  // Write new STEP file
  STEPControl_Writer writer;
  writer.Transfer(compound, STEPControl_AsIs);
  writer.Write("/home/pv/brg/code/compas_occt/translated_screws.step");
}

NB_MODULE(_step, m) {
    m.doc() = "STEP file I/O functions";
    m.def("translate_step", &translate_step, "Read STEP file, create 4 translated copies, write new STEP file");
}
