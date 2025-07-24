#include "compas.h"
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/map.h>
#include <map>
#include <iostream>

// OCCT Point includes
#include <gp_Pnt.hxx>
#include <BRepBuilderAPI_MakeVertex.hxx>
#include <TopoDS_Vertex.hxx>

// STEP I/O includes
#include <STEPCAFControl_Writer.hxx>
#include <STEPControl_Writer.hxx>
#include <IFSelect_ReturnStatus.hxx>

// XDE includes for attributes
#include <TDocStd_Document.hxx>
#include <XCAFApp_Application.hxx>
#include <XCAFDoc_DocumentTool.hxx>
#include <XCAFDoc_ShapeTool.hxx>
#include <XCAFDoc_ColorTool.hxx>
#include <TDataStd_Name.hxx>
#include <TDataStd_NamedData.hxx>
#include <TDF_Label.hxx>

// Color includes
#include <Quantity_Color.hxx>
#include <TCollection_ExtendedString.hxx>

using namespace nanobind::literals;

class Point {
public:
    Point(double x, double y, double z) : m_point(x, y, z) {}
    
    // Getters
    double x() const { return m_point.X(); }
    double y() const { return m_point.Y(); }
    double z() const { return m_point.Z(); }
    
    // STEP export with attributes support
    bool to_step(const std::string& filename, 
                 const std::string& name = "Point",
                 const std::vector<double>& color = {1.0, 0.0, 0.0}, // Default red
                 const std::map<std::string, std::string>& attributes = {}) const {
        
        std::cout << "\n=== Point STEP Export Debug ===" << std::endl;
        std::cout << "Filename: " << filename << std::endl;
        std::cout << "Name: " << name << std::endl;
        std::cout << "Color size: " << color.size() << std::endl;
        std::cout << "Attributes size: " << attributes.size() << std::endl;
        std::cout.flush();
        
        // Create XDE document for attributes support
        Handle(XCAFApp_Application) app = XCAFApp_Application::GetApplication();
        Handle(TDocStd_Document) doc;
        app->NewDocument("MDTV-XCAF", doc);
        
        Handle(XCAFDoc_ShapeTool) shapeTool = XCAFDoc_DocumentTool::ShapeTool(doc->Main());
        Handle(XCAFDoc_ColorTool) colorTool = XCAFDoc_DocumentTool::ColorTool(doc->Main());
        
        // Create vertex from point
        TopoDS_Vertex vertex = BRepBuilderAPI_MakeVertex(m_point);
        
        // Add vertex to document
        TDF_Label shapeLabel = shapeTool->AddShape(vertex, Standard_False);
        
        // Set name
        std::cout << "  Setting name: " << name << " on label" << std::endl;
        TDataStd_Name::Set(shapeLabel, name.c_str());
        
        // Set color (if provided)
        if (color.size() >= 3) {
            std::cout << "  Setting color: [" << color[0] << ", " << color[1] << ", " << color[2] << "]" << std::endl;
            Quantity_Color occtColor(color[0], color[1], color[2], Quantity_TOC_RGB);
            colorTool->SetColor(shapeLabel, occtColor, XCAFDoc_ColorSurf);
        }
        
        // Set custom attributes using the exact same pattern as step.cpp
        if (!attributes.empty()) {
            Handle(TDataStd_NamedData) namedData = TDataStd_NamedData::Set(shapeLabel);
            std::cout << "  Created NamedData handle" << std::endl;
            
            int metadataCount = 0;
            for (const auto& attr : attributes) {
                metadataCount++;
                std::cout << "    Setting metadata: " << attr.first << " = " << attr.second << std::endl;
                // Use TCollection_ExtendedString for both key and value (same as step.cpp)
                namedData->SetString(TCollection_ExtendedString(attr.first.c_str()), 
                                   TCollection_ExtendedString(attr.second.c_str()));
            }
            
            std::cout << "  Added " << metadataCount << " metadata items for point: " << name << std::endl;
        }
        
        // Export using STEPCAFControl_Writer with metadata support (same as step.cpp)
        STEPCAFControl_Writer writer;
        writer.SetColorMode(Standard_True);
        writer.SetNameMode(Standard_True);
        writer.SetLayerMode(Standard_True);
        writer.SetPropsMode(Standard_True);
        writer.SetMetadataMode(Standard_True);
        
        // Debug metadata information (same as writeCustomMetadata in step.cpp)
        std::cout << "\n=== Metadata Information ===" << std::endl;
        TDF_LabelSequence labels;
        shapeTool->GetShapes(labels);
        
        std::cout << "Found " << labels.Length() << " shapes in document" << std::endl;
        
        for (int i = 1; i <= labels.Length(); i++) {
            TDF_Label label = labels.Value(i);
            
            // Get name if it exists
            Handle(TDataStd_Name) nameAttr;
            if (label.FindAttribute(TDataStd_Name::GetID(), nameAttr)) {
                std::cout << "Shape " << i << " name: " << nameAttr->Get() << std::endl;
            } else {
                std::cout << "Shape " << i << " has no name" << std::endl;
            }
            
            // Get metadata if it exists
            Handle(TDataStd_NamedData) namedData;
            if (label.FindAttribute(TDataStd_NamedData::GetID(), namedData)) {
                std::cout << "  Found metadata on shape " << i << std::endl;
                
                // Check if containers have data
                if (!namedData->GetStringsContainer().IsEmpty()) {
                    std::cout << "  Has string attributes: " << namedData->GetStringsContainer().Size() << std::endl;
                }
            } else {
                std::cout << "  Shape " << i << " has no metadata" << std::endl;
            }
        }
        std::cout << "=== End Metadata Information ===\n" << std::endl;
        
        if (writer.Transfer(doc, STEPControl_AsIs)) {
            return writer.Write(filename.c_str()) == IFSelect_RetDone;
        }
        
        return false;
    }
    
    // String representation
    std::string __repr__() const {
        return "Point(" + std::to_string(m_point.X()) + ", " + 
               std::to_string(m_point.Y()) + ", " + 
               std::to_string(m_point.Z()) + ")";
    }

private:
    gp_Pnt m_point;
};

NB_MODULE(_point, m) {
    nb::class_<Point>(m, "Point")
        .def(nb::init<double, double, double>(), "x"_a, "y"_a, "z"_a)
        .def_prop_ro("x", &Point::x)
        .def_prop_ro("y", &Point::y)
        .def_prop_ro("z", &Point::z)
        .def("to_step", &Point::to_step, 
             "filename"_a, 
             "name"_a = "Point",
             "color"_a = std::vector<double>{1.0, 0.0, 0.0},
             "attributes"_a = std::map<std::string, std::string>{},
             "Export point to STEP file with optional name, color, and attributes")
        .def("__repr__", &Point::__repr__);
}
