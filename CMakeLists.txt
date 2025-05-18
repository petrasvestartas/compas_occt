################################################################################
#                        PROJECT CONFIGURATION
# Basic project settings and compilation flags
################################################################################

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

################################################################################
#                       EXTERNAL DEPENDENCIES SETUP
# External dependencies paths and configurations
################################################################################

# Define external directories
set(EXTERNAL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external")
set(CMAKE_MODULE_PATH "${CMAKE_MODULE_PATH};${CMAKE_CURRENT_SOURCE_DIR}/cmake")

################################################################################
#                        EIGEN LIBRARY SETUP
# Header-only linear algebra library configuration
################################################################################

set(EIGEN_INCLUDE_DIR "${EXTERNAL_DIR}/eigen")
set(EIGEN_DOWNLOAD_NEEDED FALSE)

# Check if Eigen headers exist
if(NOT EXISTS "${EIGEN_INCLUDE_DIR}/Eigen/Core")
  message(STATUS "Eigen headers not found. Will download.")
  set(EIGEN_DOWNLOAD_NEEDED TRUE)
else()
  message(STATUS "Using existing Eigen installation at: ${EIGEN_INCLUDE_DIR}")
endif()



################################################################################
#                        OCCT LIBRARY SETUP
# 3D modeling kernel configuration and path setup
################################################################################

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

################################################################################
#                    OCCT LIBRARY COMPONENTS
# OCCT component paths with proper linking order
################################################################################

# Define paths to OCCT libraries with static suffix
# Core libraries
set(OCCT_LIBRARY_KERNEL "${OCCT_INSTALL_DIR}/lib/libTKernel${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_MATH "${OCCT_INSTALL_DIR}/lib/libTKMath${CMAKE_STATIC_LIBRARY_SUFFIX}")

# Geometry and representations
set(OCCT_LIBRARY_G2D "${OCCT_INSTALL_DIR}/lib/libTKG2d${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_G3D "${OCCT_INSTALL_DIR}/lib/libTKG3d${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_GEOMBASE "${OCCT_INSTALL_DIR}/lib/libTKGeomBase${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_BREP "${OCCT_INSTALL_DIR}/lib/libTKBRep${CMAKE_STATIC_LIBRARY_SUFFIX}")

# Mid-level algorithms and topology
set(OCCT_LIBRARY_GEOMALGO "${OCCT_INSTALL_DIR}/lib/libTKGeomAlgo${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_TOPALGO "${OCCT_INSTALL_DIR}/lib/libTKTopAlgo${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_SHHEALING "${OCCT_INSTALL_DIR}/lib/libTKShHealing${CMAKE_STATIC_LIBRARY_SUFFIX}")

# Boolean operations and complex shape handling
set(OCCT_LIBRARY_MESH "${OCCT_INSTALL_DIR}/lib/libTKMesh${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_BO "${OCCT_INSTALL_DIR}/lib/libTKBO${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_PRIM "${OCCT_INSTALL_DIR}/lib/libTKPrim${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_FEAT "${OCCT_INSTALL_DIR}/lib/libTKFeat${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_OFFSET "${OCCT_INSTALL_DIR}/lib/libTKOffset${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_FILLET "${OCCT_INSTALL_DIR}/lib/libTKFillet${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_HLR "${OCCT_INSTALL_DIR}/lib/libTKHLR${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_LIBRARY_BOOL "${OCCT_INSTALL_DIR}/lib/libTKBool${CMAKE_STATIC_LIBRARY_SUFFIX}")

################################################################################
#                   DEPENDENCY MANAGEMENT TARGETS
# Custom targets for tracking build progress
################################################################################

# Create a main target to manage all external dependencies
add_custom_target(external_downloads ALL)

# Create a target to ensure OCCT libraries are ready
add_custom_target(occt_libraries_built
  COMMENT "Ensuring OCCT libraries are ready"
)

################################################################################
#             DOWNLOAD AND BUILD EXTERNAL DEPENDENCIES
# Download and build process for external libraries
################################################################################

# 1. Download Eigen if needed (header-only library)
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



################################################################################
#                OCCT DOWNLOAD AND BUILD CONFIGURATION
# OCCT build configuration with sentinel file to avoid rebuilds
################################################################################

# OCCT setup and build configuration
if(OCCT_DOWNLOAD_NEEDED)
  message(STATUS "Setting up OCCT build...")
  
  # Define a unique sentinel file to avoid rebuilding if already successful
  set(OCCT_BUILD_SENTINEL "${CMAKE_CURRENT_BINARY_DIR}/occt_build_success.txt")
  
  # Check if we've already successfully built OCCT
  if(NOT EXISTS "${OCCT_BUILD_SENTINEL}")
    message(STATUS "OCCT build needed, this will take some time...")
    # No, so we need to build OCCT from source
    ExternalProject_Add(
      occt_external
      URL https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V7_7_0.tar.gz
      PREFIX "${CMAKE_CURRENT_BINARY_DIR}/prefix"
      SOURCE_DIR "${OCCT_DIR}"
      BINARY_DIR "${OCCT_BUILD_DIR}"
      CMAKE_ARGS
        -DCMAKE_BUILD_TYPE=Release
        -DCMAKE_INSTALL_PREFIX=${OCCT_INSTALL_DIR}
        # Disable unnecessary modules to reduce build time and dependencies
        -DBUILD_MODULE_Draw=OFF
        -DBUILD_MODULE_Visualization=OFF
        -DBUILD_MODULE_ApplicationFramework=OFF
        # Disable optional dependencies we don't need
        -DUSE_RAPIDJSON=OFF
        -DUSE_TK=OFF
        -DUSE_VTK=OFF
        -DUSE_FREETYPE=OFF
        -DUSE_GL2PS=OFF
        -DUSE_OPENVR=OFF
        -DUSE_OPENGL=OFF
      # Limit parallel jobs to avoid excessive memory usage
      BUILD_COMMAND ${CMAKE_COMMAND} --build . --config Release -j 2
      BUILD_BYPRODUCTS "${OCCT_KERNEL_LIBRARY}"
      LOG_DOWNLOAD ON
      LOG_CONFIGURE ON
      LOG_BUILD ON
      LOG_INSTALL ON
      INSTALL_COMMAND ${CMAKE_COMMAND} --install . --config Release
        # Create sentinel file to mark successful build
        COMMAND ${CMAKE_COMMAND} -E touch "${OCCT_BUILD_SENTINEL}"
      UPDATE_COMMAND ""
      UPDATE_DISCONNECTED ON
    )
    add_dependencies(external_downloads occt_external)
    add_dependencies(occt_libraries_built occt_external)
  else()
    message(STATUS "OCCT previously built successfully, skipping build step.")
    # Create a dummy target when OCCT is already built
    add_custom_target(occt_external 
      COMMAND ${CMAKE_COMMAND} -E echo "Using existing OCCT build from previous run"
    )
    add_dependencies(external_downloads occt_external)
    add_dependencies(occt_libraries_built occt_external)
  endif()
else()
  # Create a dummy target when OCCT already exists
  add_custom_target(occt_external 
    COMMAND ${CMAKE_COMMAND} -E echo "Using existing OCCT installation at ${OCCT_INSTALL_DIR}"
  )
  add_dependencies(external_downloads occt_external)
  add_dependencies(occt_libraries_built occt_external)
endif()

################################################################################
#                       IMPORTED LIBRARY TARGETS
# Create imported target for OCCT kernel library and establish dependency chain
################################################################################

# Create imported target for OCCT library
add_library(occt_lib STATIC IMPORTED GLOBAL)
# Set the IMPORTED_LOCATION property to specify the location of the library
# file. This is the file that will be linked into our final executable.
set_property(TARGET occt_lib PROPERTY IMPORTED_LOCATION "${OCCT_KERNEL_LIBRARY}")
# Add a dependency to ensure the OCCT libraries are built before they are linked
add_dependencies(occt_lib occt_libraries_built)

################################################################################
#                  PYTHON AND NANOBIND CONFIGURATION
# Python bindings setup and requirements
################################################################################

# Find Python and nanobind
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module Development.SABIModule)
find_package(nanobind CONFIG REQUIRED)
find_package(Threads REQUIRED)

################################################################################
#                NANOBIND EXTENSION MODULE FUNCTION
# Function to create Python bindings with proper OCCT linking
################################################################################

# Define a function to create a Python extension module
function(create_nanobind_extension name)
  # Use nanobind to create the extension module
  nanobind_add_module(${name} 
    MODULE_NAME "${name}"           # Name of the output Python module
    STABLE_ABI                     # Use the stable ABI for Python compatibility
    ${ARGN}                        # All other arguments passed to the function
  )
  
  # Include directories for all headers needed by the extension
  target_include_directories(${name} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src   # Our own source files
    ${EIGEN_INCLUDE_DIR}              # Eigen headers
    ${OCCT_INCLUDE_DIR}               # OCCT headers
    ${nanobind_INCLUDE_DIRS}          # nanobind headers
  )
  
  # Create proper dependency chain to ensure libraries are built before linking
  add_dependencies(${name} occt_libraries_built)
  
  # Important compiler flags for OCCT
  target_compile_definitions(${name} PRIVATE
    HAVE_OPENCASCADE                  # Enable OCCT features
    OCCT_NO_PLUGINS                   # Disable plugins we don't need
  )
  
  # Use linker groups on Linux to resolve circular dependencies in OCCT
  # This is critical for proper static linking with OCCT
  if(UNIX AND NOT APPLE)
    target_link_options(${name} PRIVATE "-Wl,--no-as-needed" "-Wl,--start-group")
  endif()
  
  # Link with all OCCT libraries in the proper order
  # The order is critical due to interdependencies between OCCT components
  target_link_libraries(${name} PRIVATE
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
  
  # End linker group on Linux
  if(UNIX AND NOT APPLE)
    target_link_options(${name} PRIVATE "-Wl,--end-group")
  endif()

  # Install the extension module
  install(TARGETS ${name} DESTINATION .)
endfunction()

################################################################################
#                      MODULE CREATION AND OUTPUT
# Create extension modules and display build info
################################################################################

# Create the primitives extension module from primitives.cpp
create_nanobind_extension(_primitives src/primitives.cpp)

# Display build configuration information for debugging
message(STATUS "============= Build Configuration =============")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Standard: C++${CMAKE_CXX_STANDARD}")
message(STATUS "Eigen Include Dir: ${EIGEN_INCLUDE_DIR}")
message(STATUS "OCCT Install Dir: ${OCCT_INSTALL_DIR}")
message(STATUS "=======================================")
