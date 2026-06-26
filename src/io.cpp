// io.cpp - the `_io` extension module: STEP / IGES / STL / BREP read & write.
#include "compas.h"
#include "occt.h"

#include <nanobind/stl/map.h>

#include <map>
#include <stdexcept>
#include <string>
#include <tuple>

#include <TopoDS_Shape.hxx>
#include <BRep_Builder.hxx>
#include <BRepTools.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <STEPControl_Reader.hxx>
#include <STEPControl_Writer.hxx>
#include <STEPControl_StepModelType.hxx>
#include <STEPControl_Controller.hxx>
#include <STEPCAFControl_Reader.hxx>
#include <STEPCAFControl_Writer.hxx>
#include <IGESControl_Reader.hxx>
#include <IGESControl_Writer.hxx>
#include <IGESControl_Controller.hxx>
#include <StlAPI_Writer.hxx>
#include <Interface_Static.hxx>
#include <IFSelect_ReturnStatus.hxx>
#include <OSD.hxx>
#include <Standard_Failure.hxx>
// XDE / XCAF: STEP with names + named-data attributes (cf. OCCT PR #634)
#include <TDocStd_Document.hxx>
#include <XCAFApp_Application.hxx>
#include <XCAFDoc_DocumentTool.hxx>
#include <XCAFDoc_ShapeTool.hxx>
#include <TDataStd_Name.hxx>
#include <TDataStd_NamedData.hxx>
#include <TDataStd_HDataMapOfStringString.hxx>
#include <TDataStd_HDataMapOfStringInteger.hxx>
#include <TDataStd_HDataMapOfStringReal.hxx>
#include <TDF_Label.hxx>
#include <TDF_LabelSequence.hxx>
#include <TCollection_AsciiString.hxx>
#include <TCollection_ExtendedString.hxx>
// ---------------------------------------------------------------------------
// STEP
// ---------------------------------------------------------------------------

static Shape read_step(const std::string& filepath) {
    STEPControl_Controller::Init();  // register the STEP norm/schema (static-lib initializer is not auto-pulled)
    STEPControl_Reader reader;
    IFSelect_ReturnStatus status = reader.ReadFile(filepath.c_str());
    if (status != IFSelect_RetDone) throw std::runtime_error("Failed to read STEP file.");
    reader.TransferRoots();
    return Shape(reader.OneShape());
}

static void write_step(const Shape& s, const std::string& filepath, const std::string& unit,
                       const std::string& name, const std::string& author,
                       const std::string& organization, const std::string& description) {
    STEPControl_Controller::Init();  // register the STEP norm/schema
    (void)author;
    (void)organization;
    (void)description;  // FILE_NAME metadata not written (see write_step note below)
    try {
        STEPControl_Writer writer;
        Interface_Static::SetCVal("write.step.unit", unit.c_str());
        if (!name.empty()) Interface_Static::SetCVal("write.step.product.name", name.c_str());
        writer.Transfer(s.shape, STEPControl_AsIs);
        IFSelect_ReturnStatus status = writer.Write(filepath.c_str());
        if (status != IFSelect_RetDone) throw std::runtime_error("Failed to write STEP file.");
    } catch (const Standard_Failure& e) {
        throw std::runtime_error(std::string("STEP write failed: ") + e.GetMessageString());
    }
}

// ---------------------------------------------------------------------------
// STEP with attributes (XDE / XCAF) -- names + string/integer/real metadata.
// Mirrors OCCT PR #634: TDataStd_NamedData on the shape label is exported as
// general_property entities by STEPCAFControl_Writer (gated by PropsMode).
// ---------------------------------------------------------------------------

static inline std::string ext_to_std(const TCollection_ExtendedString& e) {
    return std::string(TCollection_AsciiString(e).ToCString());  // UTF-8
}
static inline TCollection_ExtendedString to_ext(const std::string& s) {
    return TCollection_ExtendedString(s.c_str(), Standard_True);  // s is UTF-8
}

static void write_step_with_attributes(const Shape& s, const std::string& filepath,
                                       const std::string& name,
                                       const std::map<std::string, std::string>& strings,
                                       const std::map<std::string, int>& integers,
                                       const std::map<std::string, double>& reals) {
    STEPControl_Controller::Init();
    opencascade::handle<TDocStd_Document> doc;
    XCAFApp_Application::GetApplication()->NewDocument("MDTV-XCAF", doc);
    opencascade::handle<XCAFDoc_ShapeTool> tool = XCAFDoc_DocumentTool::ShapeTool(doc->Main());

    TDF_Label label = tool->AddShape(s.shape, Standard_False);
    if (!name.empty()) TDataStd_Name::Set(label, to_ext(name));
    if (!strings.empty() || !integers.empty() || !reals.empty()) {
        opencascade::handle<TDataStd_NamedData> data = TDataStd_NamedData::Set(label);
        for (const auto& kv : strings) data->SetString(to_ext(kv.first), to_ext(kv.second));
        for (const auto& kv : integers) data->SetInteger(to_ext(kv.first), kv.second);
        for (const auto& kv : reals) data->SetReal(to_ext(kv.first), kv.second);
    }

    try {
        STEPCAFControl_Writer writer;
        writer.SetNameMode(Standard_True);
        writer.SetPropsMode(Standard_True);  // gate that emits the named-data metadata
        if (!writer.Transfer(doc, STEPControl_AsIs))
            throw std::runtime_error("Failed to transfer document to STEP.");
        if (writer.Write(filepath.c_str()) != IFSelect_RetDone)
            throw std::runtime_error("Failed to write STEP file.");
    } catch (const Standard_Failure& e) {
        throw std::runtime_error(std::string("STEP write failed: ") + e.GetMessageString());
    }
}

// (shape, name, strings, integers, reals) per free (top-level) shape in the file.
using StepRecord = std::tuple<Shape, std::string,
                              std::map<std::string, std::string>,
                              std::map<std::string, int>,
                              std::map<std::string, double>>;

static std::vector<StepRecord> read_step_with_attributes(const std::string& filepath) {
    STEPControl_Controller::Init();
    opencascade::handle<TDocStd_Document> doc;
    XCAFApp_Application::GetApplication()->NewDocument("MDTV-XCAF", doc);

    STEPCAFControl_Reader reader;
    reader.SetNameMode(Standard_True);
    reader.SetPropsMode(Standard_True);
    if (reader.ReadFile(filepath.c_str()) != IFSelect_RetDone)
        throw std::runtime_error("Failed to read STEP file.");
    if (!reader.Transfer(doc)) throw std::runtime_error("Failed to transfer STEP file.");

    opencascade::handle<XCAFDoc_ShapeTool> tool = XCAFDoc_DocumentTool::ShapeTool(doc->Main());
    TDF_LabelSequence labels;
    tool->GetFreeShapes(labels);

    std::vector<StepRecord> out;
    out.reserve(labels.Length());
    for (int i = 1; i <= labels.Length(); ++i) {
        const TDF_Label& label = labels.Value(i);
        std::string name;
        std::map<std::string, std::string> strings;
        std::map<std::string, int> integers;
        std::map<std::string, double> reals;

        opencascade::handle<TDataStd_Name> nm;
        if (label.FindAttribute(TDataStd_Name::GetID(), nm)) name = ext_to_std(nm->Get());

        opencascade::handle<TDataStd_NamedData> data;
        if (label.FindAttribute(TDataStd_NamedData::GetID(), data)) {
            if (data->HasStrings()) {
                const auto& m = data->GetStringsContainer();
                for (NCollection_DataMap<TCollection_ExtendedString, TCollection_ExtendedString>::Iterator it(m); it.More(); it.Next())
                    strings[ext_to_std(it.Key())] = ext_to_std(it.Value());
            }
            if (data->HasIntegers()) {
                const auto& m = data->GetIntegersContainer();
                for (NCollection_DataMap<TCollection_ExtendedString, Standard_Integer>::Iterator it(m); it.More(); it.Next())
                    integers[ext_to_std(it.Key())] = it.Value();
            }
            if (data->HasReals()) {
                const auto& m = data->GetRealsContainer();
                for (NCollection_DataMap<TCollection_ExtendedString, Standard_Real>::Iterator it(m); it.More(); it.Next())
                    reals[ext_to_std(it.Key())] = it.Value();
            }
        }
        out.emplace_back(Shape(tool->GetShape(label)), name, strings, integers, reals);
    }
    return out;
}

// Schema-controlled single-shape STEP export (used by OCCCurve.to_step / OCCSurface.to_step).
static void shape_to_step(const Shape& s, const std::string& filepath, const std::string& schema) {
    STEPControl_Controller::Init();
    STEPControl_Writer writer;
    Interface_Static::SetCVal("write.step.schema", schema.c_str());
    writer.Transfer(s.shape, STEPControl_AsIs);
    IFSelect_ReturnStatus status = writer.Write(filepath.c_str());
    if (status != IFSelect_RetDone) throw std::runtime_error("Failed to write STEP file.");
}

// ---------------------------------------------------------------------------
// IGES
// ---------------------------------------------------------------------------

static Shape read_iges(const std::string& filepath) {
    IGESControl_Controller::Init();
    IGESControl_Reader reader;
    IFSelect_ReturnStatus status = reader.ReadFile(filepath.c_str());
    if (status != IFSelect_RetDone) throw std::runtime_error("Failed to read IGES file.");
    reader.TransferRoots();
    return Shape(reader.OneShape());
}

static bool write_iges(const Shape& s, const std::string& filepath) {
    IGESControl_Controller::Init();
    IGESControl_Writer writer;
    if (!writer.AddShape(s.shape)) throw std::runtime_error("Failed to add shape to IGES writer.");
    writer.ComputeModel();
    return writer.Write(filepath.c_str());
}

// ---------------------------------------------------------------------------
// STL
// ---------------------------------------------------------------------------

static bool write_stl(const Shape& s, const std::string& filepath, double linear_deflection, double angular_deflection) {
    BRepMesh_IncrementalMesh mesher(s.shape, linear_deflection, Standard_False, angular_deflection, Standard_True);
    mesher.Perform();
    StlAPI_Writer writer;
    writer.ASCIIMode() = Standard_True;
    return writer.Write(s.shape, filepath.c_str());
}

// ---------------------------------------------------------------------------
// BREP
// ---------------------------------------------------------------------------

static void write_brep(const Shape& s, const std::string& filepath) {
    BRepTools::Write(s.shape, filepath.c_str());
}

static Shape read_brep(const std::string& filepath) {
    TopoDS_Shape shape;
    BRep_Builder builder;
    BRepTools::Read(shape, filepath.c_str(), builder);
    return Shape(shape);
}

void register_io(nb::module_& m) {
    OSD::SetSignal(Standard_False);  // OCCT faults -> catchable exceptions (FP masked for the host process)
    m.def("read_step", &read_step);
    m.def("write_step", &write_step,
          "shape"_a, "filepath"_a, "unit"_a = "MM", "name"_a = "", "author"_a = "", "organization"_a = "", "description"_a = "");
    m.def("write_step_with_attributes", &write_step_with_attributes,
          "shape"_a, "filepath"_a, "name"_a = "",
          "strings"_a = std::map<std::string, std::string>{},
          "integers"_a = std::map<std::string, int>{},
          "reals"_a = std::map<std::string, double>{});
    m.def("read_step_with_attributes", &read_step_with_attributes, "filepath"_a);
    m.def("edge_to_step", &shape_to_step, "shape"_a, "filepath"_a, "schema"_a = "AP203");
    m.def("face_to_step", &shape_to_step, "shape"_a, "filepath"_a, "schema"_a = "AP203");
    m.def("read_iges", &read_iges);
    m.def("write_iges", &write_iges);
    m.def("write_stl", &write_stl, "shape"_a, "filepath"_a, "linear_deflection"_a = 1e-3, "angular_deflection"_a = 0.5);
    m.def("write_brep", &write_brep);
    m.def("read_brep", &read_brep);
}
