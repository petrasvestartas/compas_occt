#include "compas.h"
#include <nanobind/stl/string.h>

// STEP I/O includes
#include <STEPControl_Reader.hxx>
#include <STEPCAFControl_Writer.hxx>
#include <STEPCAFControl_Reader.hxx>
#include <TopoDS_Shape.hxx>
#include <IFSelect_ReturnStatus.hxx>

// XDE includes for assemblies and attributes
#include <TDocStd_Document.hxx>
#include <XCAFApp_Application.hxx>
#include <XCAFDoc_DocumentTool.hxx>
#include <XCAFDoc_ShapeTool.hxx>
#include <XCAFDoc_ColorTool.hxx>
#include <XCAFDoc_LayerTool.hxx>
#include <XCAFDoc_DocumentTool.hxx>
#include <TDataStd_Name.hxx>
#include <TDataStd_Comment.hxx>
#include <TDataStd_NamedData.hxx>
#include <TDF_Label.hxx>
#include <TDF_LabelSequence.hxx>

// Transformation includes
#include <gp_Trsf.hxx>
#include <gp_Vec.hxx>
#include <BRepBuilderAPI_Transform.hxx>
#include <TopoDS_Compound.hxx>
#include <BRep_Builder.hxx>

// Color includes
#include <Quantity_Color.hxx>
#include <Quantity_NameOfColor.hxx>

// Validation properties
#include <GProp_GProps.hxx>
#include <BRepGProp.hxx>

// Shape exploration
#include <TopExp_Explorer.hxx>
#include <TopAbs_ShapeEnum.hxx>

// Tutorial
#include <TDocStd_Application.hxx>
#include <BinXCAFDrivers.hxx>
#include <BRepPrimAPI_MakeCylinder.hxx>
#include <XCAFDoc_DocumentTool.hxx>
#include <XCAFDoc_ColorTool.hxx>
#include <XCAFDoc_ShapeTool.hxx>
#include <TDF_ChildIterator.hxx>
#include <TopoDS.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <TopExp.hxx>
#include <gp_Quaternion.hxx>

TopoDS_Shape BuildWheel(const double OD, const double W){
  return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(-W/2, 0, 0), gp::DX()), OD/2, W);
}

TopoDS_Shape  BuildAxle(const double D, const double L){
  return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(-L/2, 0, 0), gp::DX()), D/2, L);
}

TopoDS_Shape BuildWheelAxle(TopoDS_Shape& wheel, TopoDS_Shape& axle, const double L){
  TopoDS_Compound compound;
  BRep_Builder builder;
  builder.MakeCompound(compound);

  gp_Trsf wheelT_right;
  wheelT_right.SetTranslationPart(gp_Vec(L/2, 0, 0));

  gp_Trsf wheelT_left;
  gp_Quaternion qn(gp::DY(), M_PI);
  gp_Trsf R;
  R.SetRotation(qn);
  wheelT_left = wheelT_left.Inverted() * R;
  wheelT_left.SetTranslationPart(gp_Vec(-L/2, 0, 0));
  
  builder.Add(compound, wheel.Moved(wheelT_right));
  builder.Add(compound, wheel.Moved(wheelT_left));
  builder.Add(compound, axle);

  return compound;
}


TopoDS_Shape BuildChassis(const TopoDS_Shape& wheelAxle, const double CL){
  TopoDS_Compound compound;
  BRep_Builder builder;
  builder.MakeCompound(compound);
  
  gp_Trsf frontT, rearT;
  frontT.SetTranslation(gp_Vec(0, CL/2, 0));
  rearT.SetTranslation(gp_Vec(0, -CL/2, 0));
  
  builder.Add(compound, wheelAxle.Moved(frontT));
  builder.Add(compound, wheelAxle.Moved(rearT));
  return compound;
}

struct t_prototype{
  TopoDS_Shape shape;
  TDF_Label label;
};

struct t_wheelPrototype : public t_prototype{
  TopoDS_Face frontFace;
  TDF_Label frontFaceLabel;
};

// bool WriteStep(const Handle(TDocStd_Document)& doc,
// const char* filename){
//   STEPCAFControl_Writer writer;
//   if (!writer.Transfer(doc, STEPControl_AsIs)) return false;
//   if (writer.Write(filename) != IFSelect_RetDone) return false;
//   return true;
// }

bool WriteStep(Handle(TDocStd_Document) doc, const std::string& filename) {
  STEPCAFControl_Writer writer;
  writer.SetColorMode(Standard_True);
  writer.SetNameMode(Standard_True);
  writer.SetLayerMode(Standard_True);
  writer.SetPropsMode(Standard_True);
  
  if (writer.Transfer(doc, STEPControl_AsIs)) {
      return writer.Write(filename.c_str()) == IFSelect_RetDone;
  }
  return false;
}

void tutorial(){

  std::cout << "Tutorial Start" << std::endl;

  Handle(TDocStd_Application) app = new TDocStd_Application;
  BinXCAFDrivers::DefineFormat(app);
  Handle(TDocStd_Document) doc;
  app->NewDocument("BinXCAF", doc);

  Handle(XCAFDoc_ShapeTool)
    ST = XCAFDoc_DocumentTool::ShapeTool(doc->Main());

    
  Handle(XCAFDoc_ColorTool)
    CT = XCAFDoc_DocumentTool::ColorTool(doc->Main());


  const double OD = 400;
  const double W = 100;
  const double D = 50;
  const double L = 500;
  const double CL = 1000;

  t_wheelPrototype wheelProto;
  wheelProto.shape = BuildWheel(OD, W);
  wheelProto.label = ST->AddShape(wheelProto.shape, false);


  t_prototype axleProto;
  axleProto.shape = BuildAxle(D, L);
  axleProto.label = ST->AddShape(axleProto.shape, false);

  t_prototype wheelAxleProto;
  wheelAxleProto.shape = BuildWheelAxle(wheelProto.shape, axleProto.shape, L);
  wheelAxleProto.label = ST->AddShape(wheelAxleProto.shape, true);

  t_prototype chassisProto;
  chassisProto.shape = BuildChassis(wheelAxleProto.shape, CL);
  chassisProto.label = ST->AddShape(chassisProto.shape, true);

  TDataStd_Name::Set(wheelProto.label, "wheel");
  TDataStd_Name::Set(axleProto.label, "axle");
  TDataStd_Name::Set(wheelAxleProto.label, "wheelAxle");
  TDataStd_Name::Set(chassisProto.label, "chassis");

  // for (TDF_ChildIterator cit(chassisProto.label); cit.More(); cit.Next()) {
  //   TDF_Label componentLabel = cit.Value();
  //   TDataStd_Name::Set(componentLabel, "wheel_axle_instance");
  // }
  // Find actual component references (not just direct children)
  TDF_LabelSequence components;
  ST->GetComponents(chassisProto.label, components);
  for (int i = 1; i <= components.Length(); i++) {
      TDF_Label componentRef = components.Value(i);
      TDataStd_Name::Set(componentRef, "wheel_axle_instance");
  }
  // Set different colors on different components, not the same label twice
  CT->SetColor(wheelProto.label, Quantity_Color(1, 0, 0, Quantity_TOC_RGB), XCAFDoc_ColorGen);  // Red wheel
  CT->SetColor(axleProto.label, Quantity_Color(0, 1, 0, Quantity_TOC_RGB), XCAFDoc_ColorGen);   // Green axle
  CT->SetColor(wheelAxleProto.label, Quantity_Color(0, 0, 1, Quantity_TOC_RGB), XCAFDoc_ColorGen); // Blue assembly
  
  TopTools_IndexedMapOfShape allWheelFaces;
  TopExp::MapShapes(wheelProto.shape, TopAbs_FACE, allWheelFaces);

  wheelProto.frontFace = TopoDS::Face(allWheelFaces(2));
  wheelProto.frontFaceLabel = ST->AddSubShape(wheelProto.label, wheelProto.frontFace);
  CT->SetColor(wheelProto.frontFaceLabel, Quantity_Color(0, 0, 1, Quantity_TOC_RGB), XCAFDoc_ColorSurf);   // Green axle
 

  
  
  PCDM_StoreStatus status = app->SaveAs(doc, "C:\\brg\\code\\compas_occt\\data\\tutorial.xbf");

  if (status != PCDM_SS_OK) {
    std::cout << "Failed to save document" << std::endl;
    return;
  }

  if (!WriteStep(doc, "C:\\brg\\code\\compas_occt\\data\\tutorial.step")) {
    std::cout << "Failed to write STEP file" << std::endl;
    return;
  }

  std::cout << "Tutorial End" << std::endl;
  

}



void assemble(const std::string& input_path, const std::string& output_path) {

  Handle(XCAFApp_Application) app = XCAFApp_Application::GetApplication();   // Create XDE document for assembly with attributes
  Handle(TDocStd_Document) doc;
  app->NewDocument("MDTV-XCAF", doc);
  
  Handle(XCAFDoc_ShapeTool) shapeTool = XCAFDoc_DocumentTool::ShapeTool(doc->Main()); // Get shape and color tools
  Handle(XCAFDoc_ColorTool) colorTool = XCAFDoc_DocumentTool::ColorTool(doc->Main());
  Handle(XCAFDoc_LayerTool) layerTool = XCAFDoc_DocumentTool::LayerTool(doc->Main()); // Get layer tool
  
  STEPControl_Reader reader; // Read original STEP file
  IFSelect_ReturnStatus status = reader.ReadFile(input_path.c_str());
  if (status != IFSelect_RetDone) return;
  
  reader.TransferRoots();
  TopoDS_Shape original = reader.Shape(1);
  if (original.IsNull()) return;
  
  // No assembly compound - use individual components only to avoid duplicates
  // Define positions and properties for 4 components with ingredient names
  double positions[4][3] = {{0, 0, 0}, {10, 0, 0}, {0, 10, 0}, {10, 10, 0}};
  std::string ingredientNames[4] = {"Carrot", "Pepper", "Onion", "Celery"};
  Quantity_NameOfColor colors[4] = {Quantity_NOC_ORANGE, Quantity_NOC_RED, Quantity_NOC_PURPLE, Quantity_NOC_GREEN};
  
  // Create layers for each ingredient
  TDF_Label layers[4];
  for (int i = 0; i < 4; i++) {
    std::string layerName = ingredientNames[i] + "_Layer";
    layers[i] = layerTool->AddLayer(layerName.c_str());
  }
  
  std::vector<TopoDS_Shape> transformedShapes;
  
  // Add the original shape as a reference shape (to be reused)
  TDF_Label originalShapeLabel = shapeTool->AddShape(original, Standard_False);
  
  // Create main assembly with a compound to ensure it has geometry
  TopoDS_Compound assemblyCompound;
  BRep_Builder builder;
  builder.MakeCompound(assemblyCompound);
  
  // Create assembly label and add the compound
  TDF_Label assemblyLabel = shapeTool->AddShape(assemblyCompound, Standard_True);
  TDataStd_Name::Set(assemblyLabel, "Chicken Soup Assembly");
  TDataStd_Comment::Set(assemblyLabel, "COMPAS OCCT Example by Petras Vestartas - 19-07-2025");
  
  // Create transformed instances and add them as assembly components
  std::vector<TDF_Label> componentLabels;
  for (int i = 0; i < 4; i++) {
    gp_Trsf transform; // Create transformation for this instance
    transform.SetTranslation(gp_Vec(positions[i][0], positions[i][1], positions[i][2]));
    
    // Create transformed shape and add to compound
    BRepBuilderAPI_Transform transformer(original, transform);
    TopoDS_Shape transformed = transformer.Shape();
    builder.Add(assemblyCompound, transformed);
    transformedShapes.push_back(transformed);
    
    // Add component with transformation (proper assembly structure)
    TDF_Label componentLabel = shapeTool->AddComponent(assemblyLabel, originalShapeLabel, transform);
    
    // Set component name (won't export to STEP but good for internal XDE structure)
    std::string componentName = ingredientNames[i] + " - Soup Ingredient";
    TDataStd_Name::Set(componentLabel, componentName.c_str());
    
    // Assign color to the component
    Quantity_Color color(colors[i]);
    colorTool->SetColor(componentLabel, color, XCAFDoc_ColorSurf);
    
    // Assign component to its layer
    layerTool->SetLayer(componentLabel, layers[i]);
    
    componentLabels.push_back(componentLabel);
  }
  
  // Write STEP file with XDE (preserves assembly structure and attributes)
  STEPCAFControl_Writer writer;
  
  // Configure writer modes (like pythonocc does)
  writer.SetColorMode(Standard_True);   // Export colors
  writer.SetNameMode(Standard_True);    // Export names
  writer.SetLayerMode(Standard_True);   // Export layers
  writer.SetPropsMode(Standard_True);   // Export properties
  
  if (writer.Transfer(doc, STEPControl_AsIs)) {
    writer.Write(output_path.c_str());
  }
}



NB_MODULE(_step, m) {
    m.doc() = "STEP file I/O functions";
    m.def("assemble", &assemble, "Read STEP file, create assembly with 4 translated copies including attributes (names, colors, validation properties)", "input_path"_a, "output_path"_a);
    m.def("tutorial", &tutorial, "Tutorial function");
}
