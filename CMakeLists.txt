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

# Setting DOWNLOAD_EXTRACT_TIMESTAMP to suppress newer CMake warnings
if(POLICY CMP0135)
    cmake_policy(SET CMP0135 NEW)
endif()

include(ExternalProject)

# ------------------------------------------------------------------------------
# Optional: Build Eigen if not found
# ------------------------------------------------------------------------------
find_path(EIGEN_INCLUDE_DIR Eigen/Core)
if(NOT EIGEN_INCLUDE_DIR)
    set(EIGEN_DIR ${CMAKE_BINARY_DIR}/eigen-src)
    ExternalProject_Add(
        eigen_ext
        URL https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip
        PREFIX ${CMAKE_BINARY_DIR}/deps/eigen
        SOURCE_DIR ${EIGEN_DIR}
        CONFIGURE_COMMAND ""
        BUILD_COMMAND ""
        INSTALL_COMMAND ""
        BUILD_BYPRODUCTS ${EIGEN_DIR}/Eigen/Core
    )
    set(EIGEN_TARGET eigen_ext)
else()
    set(EIGEN_DIR ${EIGEN_INCLUDE_DIR})
    # Create a dummy target to handle dependencies when Eigen is already installed
    add_custom_target(eigen_ext)
    set(EIGEN_TARGET eigen_ext)
endif()

# ------------------------------------------------------------------------------
# Optional: Build OCCT if not found
# ------------------------------------------------------------------------------
find_path(OCCT_INCLUDE_DIR opencascade/TKernel.hxx)
find_library(TKernel_LIB TKernel)

# Create needed directories
set(DEPS_DIR ${CMAKE_BINARY_DIR}/deps)
set(OCCT_PREFIX ${DEPS_DIR}/occt)
set(OCCT_SRC_DIR ${OCCT_PREFIX}/src/occt)
set(OCCT_BUILD_DIR ${OCCT_PREFIX}/src/occt-build)
set(OCCT_INSTALL_DIR ${OCCT_PREFIX}/install)

# List of expected OCCT static libraries
set(OCCT_LIB_TARGETS
    ${OCCT_INSTALL_DIR}/lib/libTKBool.a
    ${OCCT_INSTALL_DIR}/lib/libTKFillet.a
    ${OCCT_INSTALL_DIR}/lib/libTKOffset.a
    ${OCCT_INSTALL_DIR}/lib/libTKFeat.a
    ${OCCT_INSTALL_DIR}/lib/libTKPrim.a
    ${OCCT_INSTALL_DIR}/lib/libTKBO.a
    ${OCCT_INSTALL_DIR}/lib/libTKMesh.a
    ${OCCT_INSTALL_DIR}/lib/libTKHLR.a
    ${OCCT_INSTALL_DIR}/lib/libTKShHealing.a
    ${OCCT_INSTALL_DIR}/lib/libTKTopAlgo.a
    ${OCCT_INSTALL_DIR}/lib/libTKGeomAlgo.a
    ${OCCT_INSTALL_DIR}/lib/libTKBRep.a
    ${OCCT_INSTALL_DIR}/lib/libTKGeomBase.a
    ${OCCT_INSTALL_DIR}/lib/libTKG3d.a
    ${OCCT_INSTALL_DIR}/lib/libTKG2d.a
    ${OCCT_INSTALL_DIR}/lib/libTKMath.a
    ${OCCT_INSTALL_DIR}/lib/libTKernel.a
)

if(NOT OCCT_INCLUDE_DIR OR NOT TKernel_LIB)
    # Build OCCT from source
    ExternalProject_Add(
        occt
        URL https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V7_9_0.zip
        PREFIX ${OCCT_PREFIX}
        SOURCE_DIR ${OCCT_SRC_DIR}
        BINARY_DIR ${OCCT_BUILD_DIR}
        CMAKE_ARGS
            -DCMAKE_INSTALL_PREFIX=${OCCT_INSTALL_DIR}
            -DCMAKE_BUILD_TYPE=Release
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
        # Set LOG options for better debugging
        LOG_DOWNLOAD ON
        LOG_CONFIGURE ON
        LOG_BUILD ON
        LOG_INSTALL ON
        # Build byproducts are the OCCT libraries we need
        BUILD_BYPRODUCTS ${OCCT_LIB_TARGETS}
    )

    set(OCCT_INCLUDE_DIR ${OCCT_INSTALL_DIR}/include/opencascade)
    set(OCCT_LIB_DIR ${OCCT_INSTALL_DIR}/lib)
    set(OCCT_TARGET occt)
    
    # Create a file that marks OCCT as built to avoid rebuilding it
    file(MAKE_DIRECTORY ${DEPS_DIR})
    file(WRITE ${DEPS_DIR}/occt_built.marker "OCCT built")
else()
    # If OCCT was found, use it
    get_filename_component(OCCT_LIB_DIR ${TKernel_LIB} DIRECTORY)
    
    # Create dummy target for dependency tracking
    add_custom_target(occt)
    set(OCCT_TARGET occt)
    
    # Define the library targets for consistency with the build case
    set(OCCT_LIB_TARGETS
        ${OCCT_LIB_DIR}/libTKBool.a
        ${OCCT_LIB_DIR}/libTKFillet.a
        ${OCCT_LIB_DIR}/libTKOffset.a
        ${OCCT_LIB_DIR}/libTKFeat.a
        ${OCCT_LIB_DIR}/libTKPrim.a
        ${OCCT_LIB_DIR}/libTKBO.a
        ${OCCT_LIB_DIR}/libTKMesh.a
        ${OCCT_LIB_DIR}/libTKHLR.a
        ${OCCT_LIB_DIR}/libTKShHealing.a
        ${OCCT_LIB_DIR}/libTKTopAlgo.a
        ${OCCT_LIB_DIR}/libTKGeomAlgo.a
        ${OCCT_LIB_DIR}/libTKBRep.a
        ${OCCT_LIB_DIR}/libTKGeomBase.a
        ${OCCT_LIB_DIR}/libTKG3d.a
        ${OCCT_LIB_DIR}/libTKG2d.a
        ${OCCT_LIB_DIR}/libTKMath.a
        ${TKernel_LIB}
    )
endif()

# ------------------------------------------------------------------------------
# Build nanobind Python modules
# ------------------------------------------------------------------------------

# Define a function to add a module with proper dependencies
function(add_nanobind_module module_name source_file)
    # Create the nanobind module
    nanobind_add_module(${module_name} ${source_file})
    
    # Add include directories
    target_include_directories(${module_name} PRIVATE
        ${EIGEN_DIR}
        ${OCCT_INCLUDE_DIR}
    )
    
    # Explicitly add dependencies on external projects
    add_dependencies(${module_name} ${EIGEN_TARGET})
    add_dependencies(${module_name} ${OCCT_TARGET})
    
    # OCCT needs libraries to be linked in specific order to handle circular dependencies
    foreach(lib_target ${OCCT_LIB_TARGETS})
        # Make sure library path exists for CMake
        if(NOT EXISTS "${lib_target}")
            # Create a fake static library file to avoid CMake errors
            # with linking to non-existent files during configuration
            get_filename_component(lib_dir ${lib_target} DIRECTORY)
            file(MAKE_DIRECTORY ${lib_dir})
            
            # Create an empty file if it doesn't exist
            if(NOT EXISTS "${lib_target}")
                file(TOUCH ${lib_target})
            endif()
        endif()
    endforeach()
    
    # Link to all the OCCT libraries in the correct order
    target_link_libraries(${module_name} PRIVATE ${OCCT_LIB_TARGETS})
    
    # Install the target
    install(TARGETS ${module_name} LIBRARY DESTINATION compas_occt)
endfunction()

# Add the nanobind modules
add_nanobind_module(_primitives src/primitives.cpp)
add_nanobind_module(_curves src/curves.cpp)


