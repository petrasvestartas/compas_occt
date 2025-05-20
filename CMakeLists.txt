cmake_minimum_required(VERSION 3.15)
project(compas_occt LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ------------------------------------------------------------------------------
# Find Python and nanobind
# ------------------------------------------------------------------------------
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module Development.SABIModule)
execute_process(COMMAND ${Python_EXECUTABLE} -m nanobind --cmake_dir
                OUTPUT_VARIABLE nanobind_DIR OUTPUT_STRIP_TRAILING_WHITESPACE)
find_package(nanobind CONFIG REQUIRED PATHS ${nanobind_DIR})
find_package(Threads REQUIRED)
include(ExternalProject)

# ------------------------------------------------------------------------------
# Optional: Build Eigen if not found
# ------------------------------------------------------------------------------
find_path(EIGEN_INCLUDE_DIR Eigen/Core)
if(NOT EIGEN_INCLUDE_DIR)
    include(ExternalProject)
    set(EIGEN_DIR ${CMAKE_BINARY_DIR}/eigen-src)
    ExternalProject_Add(eigen
        URL https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip
        SOURCE_DIR ${EIGEN_DIR}
        CONFIGURE_COMMAND "" BUILD_COMMAND "" INSTALL_COMMAND ""
    )
    add_custom_target(eigen_target DEPENDS eigen)
else()
    set(EIGEN_DIR ${EIGEN_INCLUDE_DIR})
endif()

# ------------------------------------------------------------------------------
# Optional: Build OCCT if not found
# ------------------------------------------------------------------------------
find_path(OCCT_INCLUDE_DIR TKernel.hxx PATH_SUFFIXES opencascade)
find_library(TKernel_LIB TKernel)

if(NOT OCCT_INCLUDE_DIR OR NOT TKernel_LIB)
    set(OCCT_INSTALL_DIR ${CMAKE_BINARY_DIR}/occt-install)
    ExternalProject_Add(occt
        URL https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V7_9_0.zip
        SOURCE_DIR ${CMAKE_BINARY_DIR}/occt-src
        BINARY_DIR ${CMAKE_BINARY_DIR}/occt-build
        INSTALL_DIR ${OCCT_INSTALL_DIR}
        CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=${OCCT_INSTALL_DIR}
                   -DBUILD_LIBRARY_TYPE=Static
                   -DBUILD_MODULE_Draw=OFF
                   -DBUILD_MODULE_ApplicationFramework=OFF
                   -DBUILD_MODULE_DataExchange=OFF
                   -DBUILD_MODULE_Visualization=OFF
                   -DBUILD_SAMPLES_QT=OFF
                   -DBUILD_MODULE_Modeling=ON
                   -DBUILD_USE_PCH=OFF
        # Limit parallel builds to prevent memory issues, especially with BRepApprox
        BUILD_COMMAND ${CMAKE_COMMAND} --build . --config Release -j2
        INSTALL_COMMAND ${CMAKE_COMMAND} --install . --config Release
    )
    set(OCCT_INCLUDE_DIR ${OCCT_INSTALL_DIR}/include/opencascade)
    set(TKernel_LIB ${OCCT_INSTALL_DIR}/lib/libTKernel.a)
    add_custom_target(occt_target DEPENDS occt)
endif()

# ------------------------------------------------------------------------------
# Build nanobind Python modules
# ------------------------------------------------------------------------------
# Directly define each module with its source file
nanobind_add_module(_primitives src/primitives.cpp)
nanobind_add_module(_curves src/curves.cpp)

# Apply common configuration to all modules
foreach(module _primitives _curves)
    target_include_directories(${module} PRIVATE
        ${EIGEN_DIR}
        ${OCCT_INCLUDE_DIR}
    )

    # OCCT needs libraries to be linked in specific order to handle circular dependencies
    target_link_libraries(${module} PRIVATE
        # Boolean operations and features
        "${OCCT_INSTALL_DIR}/lib/libTKBool.a"
        "${OCCT_INSTALL_DIR}/lib/libTKFillet.a"
        "${OCCT_INSTALL_DIR}/lib/libTKOffset.a"
        "${OCCT_INSTALL_DIR}/lib/libTKFeat.a"
        "${OCCT_INSTALL_DIR}/lib/libTKPrim.a"
        "${OCCT_INSTALL_DIR}/lib/libTKBO.a"
        # Meshing
        "${OCCT_INSTALL_DIR}/lib/libTKMesh.a"
        "${OCCT_INSTALL_DIR}/lib/libTKHLR.a"
        "${OCCT_INSTALL_DIR}/lib/libTKShHealing.a"
        # Algorithms
        "${OCCT_INSTALL_DIR}/lib/libTKTopAlgo.a"
        "${OCCT_INSTALL_DIR}/lib/libTKGeomAlgo.a"
        # Geometry
        "${OCCT_INSTALL_DIR}/lib/libTKBRep.a"
        "${OCCT_INSTALL_DIR}/lib/libTKGeomBase.a"
        # Core
        "${OCCT_INSTALL_DIR}/lib/libTKG3d.a"
        "${OCCT_INSTALL_DIR}/lib/libTKG2d.a"
        "${OCCT_INSTALL_DIR}/lib/libTKMath.a"
        "${OCCT_INSTALL_DIR}/lib/libTKernel.a"
    )

    if(TARGET eigen)
        add_dependencies(${module} eigen_target)
    endif()
    if(TARGET occt)
        add_dependencies(${module} occt_target)
    endif()

    install(TARGETS ${module} LIBRARY DESTINATION compas_occt)
endforeach()


