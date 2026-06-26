// module.cpp - the single `compas_occt._occt` extension module.
//
// All OCCT-backed free functions live in ONE module so the whole package links exactly one
// copy of OCCT. This is required for correctness: OCCT's RTTI (Standard_Type descriptors) and
// memory manager are per-binary, so passing OCCT objects between separately-linked extensions
// breaks Handle::DownCast (e.g. STEP writing). One module is also far leaner than one OCCT copy
// per submodule.
#include "compas.h"

#include <Standard_Version.hxx>
#include <Message.hxx>
#include <Message_Messenger.hxx>
#include <Message_PrinterOStream.hxx>

void register_types(nb::module_&);
void register_geometry(nb::module_&);
void register_curves(nb::module_&);
void register_nurbscurve(nb::module_&);
void register_curve2d(nb::module_&);
void register_surfaces(nb::module_&);
void register_nurbssurface(nb::module_&);
void register_explore(nb::module_&);
void register_props(nb::module_&);
void register_make(nb::module_&);
void register_adaptor(nb::module_&);
void register_relations(nb::module_&);
void register_boolean(nb::module_&);
void register_fix(nb::module_&);
void register_meshing(nb::module_&);
void register_io(nb::module_&);

NB_MODULE(_occt, m) {
    m.doc() = "Direct nanobind bindings of OCCT 8 (single module, one OCCT copy).";
    // Keep OCCT's console chatter (transfer statistics, etc.) out of the Python stdout;
    // operations report success/failure through their return values.
    Message::DefaultMessenger()->RemovePrinters(STANDARD_TYPE(Message_PrinterOStream));
    register_types(m);
    register_geometry(m);
    register_curves(m);
    register_nurbscurve(m);
    register_curve2d(m);
    register_surfaces(m);
    register_nurbssurface(m);
    register_explore(m);
    register_props(m);
    register_make(m);
    register_adaptor(m);
    register_relations(m);
    register_boolean(m);
    register_fix(m);
    register_meshing(m);
    register_io(m);
    m.def("occt_version", []() { return std::string(OCC_VERSION_STRING_EXT); });
}
