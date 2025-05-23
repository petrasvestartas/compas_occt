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
set(CMAKE_DEPS_DIR ${CMAKE_BINARY_DIR}/deps)
set(OCCT_PREFIX ${CMAKE_DEPS_DIR}/occt) # Create needed directories
file(MAKE_DIRECTORY ${CMAKE_DEPS_DIR})
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
set(OCCT_MODULES TKBool TKFillet TKOffset TKFeat TKPrim TKBO TKMesh TKHLR TKShHealing TKTopAlgo TKGeomAlgo TKBRep TKGeomBase TKG3d TKG2d TKMath TKernel)
foreach(MODULE ${OCCT_MODULES})
    list(APPEND OCCT_LIB_TARGETS "${OCCT_LIB_DIR}/${LIB_PREFIX}${MODULE}${LIB_EXT}")
endforeach()

add_custom_target(occt_ext) # This two-target approach solves the issue of first downloading then building our libraries

if(NOT EXISTS "${OCCT_INSTALL_DIR}/my_include" OR NOT EXISTS "${OCCT_INSTALL_DIR}/my_static_libs")
    ExternalProject_Add(
        occt_download
        URL https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V7_9_0.zip
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
            -DBUILD_MODULE_Draw=OFF
            -DBUILD_MODULE_ApplicationFramework=OFF
            -DBUILD_MODULE_DataExchange=OFF
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

function(add_nanobind_module module_name source_file)
    nanobind_add_module(${module_name} ${source_file})                                          # Creates the Python extension module with nanobind
    target_include_directories(${module_name} SYSTEM PRIVATE ${EIGEN_DIR} ${OCCT_INCLUDE_DIR})  # Add include paths for headers (SYSTEM suppresses warnings)
    add_dependencies(${module_name} eigen_ext occt_ext)                                         # Ensures Eigen and OCCT are built before this module
    target_link_libraries(${module_name} PRIVATE ${OCCT_LIB_TARGETS})                           # Links against all the OCCT static libraries
    install(TARGETS ${module_name} LIBRARY DESTINATION compas_occt)                             # Installs the compiled module to the compas_occt package
endfunction()

add_nanobind_module(_primitives src/primitives.cpp)
add_nanobind_module(_curves src/curves.cpp)
add_nanobind_module(_nurbssurface src/nurbssurface.cpp)