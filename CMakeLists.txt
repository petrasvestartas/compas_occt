cmake_minimum_required(VERSION 3.15)
project(compas_occt LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(ExternalProject)
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module Development.SABIModule)
find_package(nanobind CONFIG REQUIRED)
find_package(Threads REQUIRED)

# ------------------------------------------------------------------------------
# Eigen (header-only library)
# ------------------------------------------------------------------------------
set(EIGEN_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external/eigen")
file(MAKE_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/external") # Create directories if they don't exist
add_custom_target(eigen_ext) # This two-target approach solves the issue of first downloading then building our libraries
message(STATUS "---------------------- Eigen: ${EIGEN_DIR}")

if(NOT EXISTS "${EIGEN_DIR}/Eigen")
    ExternalProject_Add(
        eigen_download
        URL https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip
        PREFIX ${CMAKE_BINARY_DIR}/deps/eigen
        SOURCE_DIR ${EIGEN_DIR}
        CONFIGURE_COMMAND ""
        BUILD_COMMAND ""
        INSTALL_COMMAND ""
        TEST_COMMAND ""
    )
    add_dependencies(eigen_ext eigen_download)
endif()

# ------------------------------------------------------------------------------
# OCCT (static libraries)
# ------------------------------------------------------------------------------
# OCCT is cached under external/ (like Eigen) so it survives `build/` cleans and is not
# re-downloaded / rebuilt every time (the OCCT build is the 30-60 min long pole).
set(OCCT_PREFIX ${CMAKE_CURRENT_SOURCE_DIR}/external/occt)
file(MAKE_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/external)
set(OCCT_SRC_DIR ${OCCT_PREFIX}/src/occt)
set(OCCT_BUILD_DIR ${OCCT_PREFIX}/src/occt-build)
set(OCCT_INSTALL_DIR ${OCCT_PREFIX}/install) # Use the same custom install path as specified in ExternalProject_Add
set(OCCT_INCLUDE_DIR "${OCCT_INSTALL_DIR}/my_include" CACHE PATH "Path to OCCT headers" FORCE) # Use the same custom include path as specified in ExternalProject_Add
set(OCCT_LIB_DIR "${OCCT_INSTALL_DIR}/my_static_libs" CACHE PATH "Path to OCCT libraries" FORCE)

message(STATUS "---------------------- OCCT_INCLUDE_DIR: ${OCCT_INCLUDE_DIR}")
message(STATUS "---------------------- OCCT_LIB_DIR: ${OCCT_LIB_DIR}")

if(WIN32)
    set(LIB_PREFIX "")
    set(LIB_EXT ".lib")
else()
    set(LIB_PREFIX "lib")
    set(LIB_EXT ".a")
endif()

# OCCT has many static libraries. Generate the library targets list using OCCT_LIB_DIR.
set(OCCT_LIB_TARGETS "")
# High-level -> low-level ordering for single-pass linkers. DataExchange toolkits
# (STEP/IGES/STL + Interface_Static/APIHeaderSection) -> TKDE*/TKXSBase. Bounding-box classes
# need NO separate toolkit in OCCT 8.0: Bnd -> TKMath, BndLib -> TKGeomBase, BRepBndLib -> TKTopAlgo
# (there is no TKBnd toolkit).
set(OCCT_MODULES
    TKDESTEP TKDEIGES TKDESTL TKDE TKXSBase
    # CAF / XDE toolkits: OCCT 8.0 bundles XDE-based STEPCAFControl_* + DESTEP_Provider into
    # TKDESTEP, so these are referenced transitively by the STEP read/write path. They are
    # auto-built as DataExchange dependencies even with ApplicationFramework OFF.
    TKBinXCAF TKXmlXCAF TKXCAF TKVCAF TKCAF TKLCAF
    TKBin TKBinL TKBinTObj TKXml TKXmlL TKXmlTObj TKStd TKStdL TKTObj TKCDF
    # TKXCAF (XCAFDoc_VisMaterial) pulls Graphic3d_* material symbols from the
    # Visualization layer; TKV3d + TKService satisfy them (no OpenGL/driver needed).
    TKV3d TKService
    TKBool TKFillet TKOffset TKFeat TKPrim TKBO TKMesh TKHLR
    TKShHealing TKTopAlgo TKGeomAlgo TKBRep TKGeomBase TKG3d TKG2d TKMath TKernel)
foreach(MODULE ${OCCT_MODULES})
    list(APPEND OCCT_LIB_TARGETS "${OCCT_LIB_DIR}/${LIB_PREFIX}${MODULE}${LIB_EXT}")
endforeach()

add_custom_target(occt_ext) # This two-target approach solves the issue of first downloading then building our libraries

if(NOT EXISTS "${OCCT_INSTALL_DIR}/my_include" OR NOT EXISTS "${OCCT_INSTALL_DIR}/my_static_libs")
    ExternalProject_Add(
        occt_download
        # URL https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V7_9_1.zip
        # Latest OCCT 8: V8_0_0_p1 (8.0.0 patch 1) - newer than the V8_0_0 release and the
        # rc1..rc5 candidates; matches the local clone at C:/brg/OCCT (git describe = V8_0_0_p1).
        URL https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V8_0_0_p1.zip
        PREFIX ${OCCT_PREFIX}
        SOURCE_DIR ${OCCT_SRC_DIR}
        BINARY_DIR ${OCCT_BUILD_DIR}
        CMAKE_ARGS
            -DCMAKE_INSTALL_PREFIX=${OCCT_INSTALL_DIR}
            # Use OCCT-specific install directory variables without quotes
            -DINSTALL_DIR_LIB=my_static_libs 
            -DINSTALL_DIR_INCLUDE=my_include 
            -DINSTALL_DIR_LAYOUT=Unix
            # Other build options
            -DCMAKE_BUILD_TYPE=Release
            -DBUILD_LIBRARY_TYPE=Static
            # OCCT requires FreeType by default (font/text rendering); we don't ship it and
            # Visualization is OFF, so disable the dependency to avoid a hard configure error.
            -DUSE_FREETYPE=OFF
            -DBUILD_MODULE_Draw=OFF
            -DBUILD_MODULE_ApplicationFramework=OFF
            # DataExchange ON: STEP/IGES/STL import+export (OCCBrep.to_step/from_step/...).
            -DBUILD_MODULE_DataExchange=ON
            # Visualization stays OFF: tessellation is reimplemented on BRepMesh (no ShapeTesselator).
            -DBUILD_MODULE_Visualization=OFF
            -DBUILD_SAMPLES_QT=OFF
            -DBUILD_USE_PCH=ON
        # Must build AND install the libraries to the custom location
        BUILD_COMMAND ${CMAKE_COMMAND} --build . --config Release # -j4
        INSTALL_COMMAND ${CMAKE_COMMAND} --install . --config Release
        BUILD_BYPRODUCTS ${OCCT_LIB_TARGETS}
    )
    
    add_dependencies(occt_ext occt_download)
endif()

# ------------------------------------------------------------------------------
# Build nanobind Python modules
# ------------------------------------------------------------------------------

# Variadic: a module may be built from several .cpp files (e.g. _brep, _curves).
function(add_nanobind_module module_name)
    # STABLE_ABI is REQUIRED to match `wheel.py-api = "cp312"` in pyproject.toml. Without it,
    # nanobind builds a version-specific extension (e.g. _occt.cp312-win_amd64.pyd) while
    # scikit-build-core still tags the wheel `cp312-abi3`. cibuildwheel then tests that single
    # wheel on cp313/cp314, where Python refuses to load a cp312-tagged .pyd -> the
    # "cannot import name '_occt'" failure. With STABLE_ABI, nanobind emits a true abi3 module
    # (_occt.abi3.so / _occt.pyd) on Python >=3.12 and silently falls back to a version-specific
    # build on older Pythons (which scikit-build-core then tags correctly per version).
    nanobind_add_module(${module_name} STABLE_ABI ${ARGN})                                                   # Creates the Python extension module with nanobind
    target_include_directories(${module_name} SYSTEM PRIVATE ${EIGEN_DIR} ${OCCT_INCLUDE_DIR})              # External headers (SYSTEM suppresses warnings)
    target_include_directories(${module_name} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src)                       # Our own headers (compas.h, handles.h, occt.h)
    add_dependencies(${module_name} eigen_ext occt_ext)                                                      # Ensures Eigen and OCCT are built first
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang" AND NOT APPLE AND NOT MSVC)
        # GNU ld is order-sensitive and OCCT static libs have cyclic deps -> wrap in a group.
        target_link_libraries(${module_name} PRIVATE -Wl,--start-group ${OCCT_LIB_TARGETS} -Wl,--end-group)
    else()
        # MSVC link is multi-pass and Apple ld64 is order-insensitive: a flat list is fine
        # (and ld64 does not understand --start-group/--end-group).
        target_link_libraries(${module_name} PRIVATE ${OCCT_LIB_TARGETS})
    endif()
    if(WIN32)
        # OCCT TKernel (OSD_Host/OSD_File) uses Winsock + Win32 system APIs; static OCCT does
        # not carry these, so link the system import libraries ourselves.
        target_link_libraries(${module_name} PRIVATE ws2_32 advapi32 user32 gdi32 shell32 ole32)
    elseif(APPLE)
        # TKService/TKV3d (Visualization, linked for the XDE STEP-attributes path) reference the
        # Cocoa/OpenGL/IOKit frameworks on macOS, even though we never open a display.
        target_link_libraries(${module_name} PRIVATE "-framework Cocoa" "-framework OpenGL" "-framework IOKit")
    elseif(UNIX)
        # ... and the X11 + GL shared libraries on Linux.
        find_package(X11)
        target_link_libraries(${module_name} PRIVATE ${X11_LIBRARIES} GL)
    endif()
    install(TARGETS ${module_name} LIBRARY DESTINATION compas_occt)                                          # Installs into the compas_occt package
endfunction()

# A SINGLE extension module: links OCCT exactly once (correctness - shared RTTI/memory across
# the whole API - and far leaner than one OCCT copy per submodule).
add_nanobind_module(_occt
    src/module.cpp
    src/types.cpp
    src/geometry.cpp
    src/curves.cpp src/nurbscurve.cpp src/curve2d.cpp
    src/surfaces.cpp src/nurbssurface.cpp
    src/brep_explore.cpp src/brep_props.cpp src/brep_make.cpp src/brep_adaptor.cpp src/brep_relations.cpp src/brep_boolean.cpp src/brep_fix.cpp
    src/meshing.cpp
    src/io.cpp)

