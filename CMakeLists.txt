cmake_minimum_required(VERSION 3.15)
project(compas_occt LANGUAGES CXX)

# Build configuration
set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
set(CMAKE_CXX_STANDARD 20 CACHE STRING "C++ standard to use for the build." FORCE)
set(CMAKE_CXX_STANDARD_REQUIRED ON CACHE BOOL "Require the specified C++ standard." FORCE)
set(CMAKE_CXX_EXTENSIONS OFF CACHE BOOL "Disable compiler-specific extensions." FORCE)

# For Python compatibility, ensure ABI compatibility with libstdc++
if(CMAKE_COMPILER_IS_GNUCXX)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D_GLIBCXX_USE_CXX11_ABI=0")
endif()

include(ExternalProject)

# External dependencies will be placed in the build directory to keep the src tree clean
set(EXTERNAL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external")
set(CMAKE_MODULE_PATH "${CMAKE_MODULE_PATH};${CMAKE_CURRENT_SOURCE_DIR}/cmake")

# -------------------- Eigen header-only library --------------------------
# Eigen is a header-only library, so we only need to download it once
set(EIGEN_INCLUDE_DIR "${EXTERNAL_DIR}/eigen")
set(EIGEN_DOWNLOAD_NEEDED FALSE)

# Check if Eigen folder exists
if (NOT EXISTS "${EIGEN_INCLUDE_DIR}/Eigen/Core")
  message(STATUS "Eigen headers not found. Will download.")
  set(EIGEN_DOWNLOAD_NEEDED TRUE)
else()
  message(STATUS "Using existing Eigen installation at: ${EIGEN_INCLUDE_DIR}")
endif()

# --------------- Template Static Library --------------------------
# Define paths
set(TEMPLATE_LIB_DIR "${EXTERNAL_DIR}/template_cpp_static_library")
set(TEMPLATE_LIB_BUILD_DIR "${CMAKE_CURRENT_BINARY_DIR}/template_static_lib_build")
set(TEMPLATE_LIB_LIBRARY "${TEMPLATE_LIB_BUILD_DIR}/libcpp_static_lib${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(TEMPLATE_LIB_INCLUDE_DIR "${TEMPLATE_LIB_DIR}/src")
set(TEMPLATE_LIB_DOWNLOAD_NEEDED FALSE)

# Check if template library already exists
if(NOT EXISTS "${TEMPLATE_LIB_LIBRARY}")
  message(STATUS "Template static library not found. Will download and build.")
  set(TEMPLATE_LIB_DOWNLOAD_NEEDED TRUE)
else()
  message(STATUS "Using existing template static library at: ${TEMPLATE_LIB_LIBRARY}")
endif()

# -------------------- OCCT library --------------------------
set(OCCT_DIR "${EXTERNAL_DIR}/occt")
set(OCCT_BUILD_DIR "${CMAKE_CURRENT_BINARY_DIR}/occt_build")
set(OCCT_INSTALL_DIR "${CMAKE_CURRENT_BINARY_DIR}/occt_install")
set(OCCT_INCLUDE_DIR "${OCCT_INSTALL_DIR}/include/opencascade")

# Define the key OCCT library we'll use to check if installation exists
set(OCCT_KERNEL_LIBRARY "${OCCT_INSTALL_DIR}/lib/libTKernel${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_DOWNLOAD_NEEDED FALSE)

# Check if OCCT kernel library exists as indicator for complete installation
if(NOT EXISTS "${OCCT_KERNEL_LIBRARY}")
  message(STATUS "OCCT library not found. Will download and build.")
  set(OCCT_DOWNLOAD_NEEDED TRUE)
else()
  message(STATUS "Using existing OCCT installation at: ${OCCT_INSTALL_DIR}")
endif()

# Define OCCT library paths
# Following the same pattern as template library - defining exact paths to static libraries
set(OCCT_LIBRARY_KERNEL "${OCCT_INSTALL_DIR}/lib/libTKernel${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_MATH "${OCCT_INSTALL_DIR}/lib/libTKMath${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_G2D "${OCCT_INSTALL_DIR}/lib/libTKG2d${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_G3D "${OCCT_INSTALL_DIR}/lib/libTKG3d${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_GEOMBASE "${OCCT_INSTALL_DIR}/lib/libTKGeomBase${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_BREP "${OCCT_INSTALL_DIR}/lib/libTKBRep${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_GEOMALGO "${OCCT_INSTALL_DIR}/lib/libTKGeomAlgo${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_TOPALGO "${OCCT_INSTALL_DIR}/lib/libTKTopAlgo${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_SHHEALING "${OCCT_INSTALL_DIR}/lib/libTKShHealing${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_MESH "${OCCT_INSTALL_DIR}/lib/libTKMesh${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_BO "${OCCT_INSTALL_DIR}/lib/libTKBO${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_PRIM "${OCCT_INSTALL_DIR}/lib/libTKPrim${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_FEAT "${OCCT_INSTALL_DIR}/lib/libTKFeat${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_OFFSET "${OCCT_INSTALL_DIR}/lib/libTKOffset${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_FILLET "${OCCT_INSTALL_DIR}/lib/libTKFillet${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_HLR "${OCCT_INSTALL_DIR}/lib/libTKHLR${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_BOOL "${OCCT_INSTALL_DIR}/lib/libTKBool${CMAKE_STATIC_LIBRARY_SUFFIX}")

# Create a main target to manage all external dependencies
add_custom_target(external_downloads ALL)

# Create a target to ensure OCCT libraries are ready
add_custom_target(occt_libraries_built
  COMMENT "Ensuring OCCT libraries are ready"
)

# -------------------- Download and build external dependencies --------------------
# 1. Download Eigen if needed
if(EIGEN_DOWNLOAD_NEEDED)
  message(STATUS "Downloading Eigen...")
  ExternalProject_Add(
    eigen_download
    URL https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip
    SOURCE_DIR "${EIGEN_INCLUDE_DIR}"
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ""
    INSTALL_COMMAND ""
    LOG_DOWNLOAD ON
    UPDATE_COMMAND ""
    PATCH_COMMAND ""
    TLS_VERIFY ON
  )
  add_dependencies(external_downloads eigen_download)
endif()

# 2. Template static library setup
if(TEMPLATE_LIB_DOWNLOAD_NEEDED)
  message(STATUS "Setting up template static library build...")
  ExternalProject_Add(
    template_cpp_static_library
    GIT_REPOSITORY https://github.com/petrasvestartas/template_cpp_static_library.git
    GIT_TAG main
    PREFIX "${CMAKE_CURRENT_BINARY_DIR}/prefix"
    SOURCE_DIR "${TEMPLATE_LIB_DIR}"
    BINARY_DIR "${TEMPLATE_LIB_BUILD_DIR}"
    CMAKE_ARGS -DCMAKE_BUILD_TYPE=Release
    BUILD_BYPRODUCTS "${TEMPLATE_LIB_LIBRARY}"
    LOG_DOWNLOAD ON
    LOG_CONFIGURE ON
    LOG_BUILD ON
    UPDATE_COMMAND ""
    INSTALL_COMMAND ""
    UPDATE_DISCONNECTED ON
  )
  add_dependencies(external_downloads template_cpp_static_library)
else()
  # Create a dummy target when template library exists
  add_custom_target(template_cpp_static_library 
    COMMAND ${CMAKE_COMMAND} -E echo "Using existing static library at ${TEMPLATE_LIB_LIBRARY}"
  )
  add_dependencies(external_downloads template_cpp_static_library)
endif()

# 3. OCCT setup
if(OCCT_DOWNLOAD_NEEDED)
  message(STATUS "Setting up OCCT build...")
  ExternalProject_Add(
    occt_external
    URL https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V7_9_0.zip
    PREFIX "${CMAKE_CURRENT_BINARY_DIR}/occt_prefix"
    SOURCE_DIR "${OCCT_DIR}"
    BINARY_DIR "${OCCT_BUILD_DIR}"
    CMAKE_ARGS 
      -DCMAKE_INSTALL_PREFIX=${OCCT_INSTALL_DIR}
      -DCMAKE_BUILD_TYPE=Release
      -DBUILD_LIBRARY_TYPE=Static
      -DUSE_TK=OFF
      -DUSE_VTK=OFF
      -DUSE_FREETYPE=OFF
      -DBUILD_SAMPLES_MFC=OFF
      -DBUILD_SAMPLES_QT=OFF
      -DBUILD_Inspector=OFF
      -DINSTALL_SAMPLES=OFF
      -DBUILD_USE_PCH=OFF
      -DBUILD_OPT_PROFILE=Production
      -DBUILD_MODULE_ApplicationFramework=OFF
      -DBUILD_MODULE_DataExchange=OFF
      -DBUILD_MODULE_Draw=OFF
      -DBUILD_MODULE_VisualizationTest=OFF
      -DBUILD_MODULE_Visualization=OFF
      -DUSE_OPENGL=OFF
    # Limit to 2 parallel jobs to avoid memory issues
    BUILD_COMMAND ${CMAKE_COMMAND} --build . --config Release -j 2
    INSTALL_COMMAND ${CMAKE_COMMAND} --install . --config Release
    BUILD_BYPRODUCTS
      "${OCCT_LIBRARY_KERNEL}"
      "${OCCT_LIBRARY_MATH}"
      "${OCCT_LIBRARY_G2D}"
      "${OCCT_LIBRARY_G3D}"
      "${OCCT_LIBRARY_GEOMBASE}"
      "${OCCT_LIBRARY_BREP}"
      "${OCCT_LIBRARY_GEOMALGO}"
      "${OCCT_LIBRARY_TOPALGO}"
      "${OCCT_LIBRARY_SHHEALING}"
      "${OCCT_LIBRARY_MESH}"
      "${OCCT_LIBRARY_BO}"
      "${OCCT_LIBRARY_PRIM}"
      "${OCCT_LIBRARY_FEAT}"
      "${OCCT_LIBRARY_OFFSET}"
      "${OCCT_LIBRARY_FILLET}"
      "${OCCT_LIBRARY_HLR}"
      "${OCCT_LIBRARY_BOOL}"
    LOG_DOWNLOAD ON
    LOG_CONFIGURE ON
    LOG_BUILD ON
    LOG_INSTALL ON
    UPDATE_COMMAND ""
    UPDATE_DISCONNECTED ON
  )
  add_dependencies(external_downloads occt_external)
  add_dependencies(occt_libraries_built occt_external)
else()
  # Create a dummy target when OCCT library exists
  add_custom_target(occt_external
    COMMAND ${CMAKE_COMMAND} -E echo "Using existing OCCT installation at ${OCCT_INSTALL_DIR}"
  )
  add_dependencies(external_downloads occt_external)
  add_dependencies(occt_libraries_built occt_external)
endif()

# Create imported targets for static libraries
add_library(cpp_static_lib STATIC IMPORTED GLOBAL)
set_property(TARGET cpp_static_lib PROPERTY IMPORTED_LOCATION "${TEMPLATE_LIB_LIBRARY}")
add_dependencies(cpp_static_lib template_cpp_static_library)

add_library(occt_lib STATIC IMPORTED GLOBAL)
set_property(TARGET occt_lib PROPERTY IMPORTED_LOCATION "${OCCT_KERNEL_LIBRARY}")
add_dependencies(occt_lib occt_external)

# Find Python and nanobind
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module Development.SABIModule)
find_package(nanobind CONFIG REQUIRED)
find_package(Threads REQUIRED)

# Define a function to add a nanobind module with common settings
function(add_nanobind_extension name source)
  nanobind_add_module(
    ${name}
    STABLE_ABI
    NB_STATIC
    ${source}
  )
  
  # Apply precompiled headers
  target_precompile_headers(${name} PRIVATE src/compas.h)
  
  # Include directories
  target_include_directories(${name} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${EIGEN_INCLUDE_DIR}
    ${TEMPLATE_LIB_INCLUDE_DIR}
    ${OCCT_INCLUDE_DIR}
    ${nanobind_INCLUDE_DIRS}
  )
  
  # Create proper dependency chain
  add_dependencies(${name} cpp_static_lib occt_libraries_built)
  
  # Important compiler flags for OCCT
  target_compile_definitions(${name} PRIVATE
    HAVE_OPENCASCADE
    OCCT_NO_PLUGINS
  )
  
  # For GCC/Linux, start the group to handle circular dependencies
  if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    target_link_options(${name} PRIVATE "-Wl,--no-as-needed" "-Wl,--start-group")
  endif()
  
  # Link with all libraries in the proper order
  target_link_libraries(${name} PRIVATE
    # First the template library
    cpp_static_lib
    
    # Then all OCCT libraries in proper dependency order
    # Boolean operations and complex shape handling
    "${OCCT_LIBRARY_BOOL}"
    "${OCCT_LIBRARY_FILLET}"
    "${OCCT_LIBRARY_OFFSET}"
    "${OCCT_LIBRARY_FEAT}"
    "${OCCT_LIBRARY_PRIM}"
    "${OCCT_LIBRARY_BO}"
    "${OCCT_LIBRARY_MESH}"
    "${OCCT_LIBRARY_HLR}"
    "${OCCT_LIBRARY_SHHEALING}"
    
    # Mid-level algorithms and topology
    "${OCCT_LIBRARY_TOPALGO}"
    "${OCCT_LIBRARY_GEOMALGO}"
    
    # Geometry and representations
    "${OCCT_LIBRARY_BREP}"
    "${OCCT_LIBRARY_GEOMBASE}"
    "${OCCT_LIBRARY_G3D}"
    "${OCCT_LIBRARY_G2D}"
    
    # Core libraries
    "${OCCT_LIBRARY_MATH}"
    "${OCCT_LIBRARY_KERNEL}"
  )
  
  # For GCC/Linux, end the group to handle circular dependencies
  if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    target_link_options(${name} PRIVATE "-Wl,--end-group")
  endif()
  
  # Install the module
  install(TARGETS ${name} LIBRARY DESTINATION compas_occt)
endfunction()

# Create individual extension modules for each C++ file
add_nanobind_extension(_primitives src/primitives.cpp)

# Display build configuration information
message(STATUS "============= Build Configuration =============")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Standard: C++${CMAKE_CXX_STANDARD}")
message(STATUS "Eigen Include Dir: ${EIGEN_INCLUDE_DIR}")
message(STATUS "Template Static Library: ${TEMPLATE_LIB_LIBRARY}")
message(STATUS "Template Include Dir: ${TEMPLATE_LIB_INCLUDE_DIR}")
message(STATUS "OCCT Install Dir: ${OCCT_INSTALL_DIR}")
message(STATUS "=======================================")
