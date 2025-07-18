#include "compas.h"
#include <nanobind/stl/string.h>

#include <BRepBuilderAPI_MakeEdge.hxx>
#include <gp_Pln.hxx>
#include <Geom_Plane.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Wire.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepPrimAPI_MakePrism.hxx>
#include <TopExp.hxx>
#include <TopoDS.hxx>
#include <BRepFilletAPI_MakeFillet.hxx>
#include <TopoDS_Iterator.hxx>


// Minimal OCCT includes for STEP reading
#include <STEPControl_Reader.hxx>
#include <TopoDS_Shape.hxx>
#include <IFSelect_ReturnStatus.hxx>

void assemble() {
  // Read STEP file with minimal OCCT dependencies
  const char* stepFilePath = "/home/pv/brg/code/compas_occt/data/screw.step";
  std::cout << "Reading STEP file: " << stepFilePath << std::endl;
  
  STEPControl_Reader reader;
  IFSelect_ReturnStatus status = reader.ReadFile(stepFilePath);
  if (status == IFSelect_RetDone) {
    int nbRoots = reader.TransferRoots();
    std::cout << nbRoots << " roots transferred" << std::endl;
    
    if (nbRoots > 0) {
      TopoDS_Shape shape = reader.Shape(1);
      std::cout << "First shape loaded successfully" << std::endl;
    } else {
      std::cout << "No shapes found in STEP file" << std::endl;
    }
  } else {
    std::cout << "Failed to read STEP file" << std::endl;
  }
}

NB_MODULE(_step, m) {
    m.doc() = "Minimal STEP file I/O functions";

    m.def("assemble", &assemble, "Assemble a STEP file");
}
