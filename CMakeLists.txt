cmake_minimum_required(VERSION 3.15)
project(compas_occt LANGUAGES CXX)

# Build configuration
set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
option(ENABLE_PRECOMPILED_HEADERS "Enable precompiled headers for the build" ON)

# External dependencies
include(ExternalProject)

# Setup Eigen (header-only library)
set(EXTERNAL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external")
set(EIGEN_INCLUDE_DIR "${EXTERNAL_DIR}/eigen")
set(OCCT_SOURCE_DIR "${EXTERNAL_DIR}/occt")
set(OCCT_BINARY_DIR "${EXTERNAL_DIR}/occt-build")
set(OCCT_INSTALL_DIR "${EXTERNAL_DIR}/occt-install")

# Create external downloads target
add_custom_target(external_downloads ALL)

# Download Eigen if not already present
if(NOT EXISTS "${EIGEN_INCLUDE_DIR}")
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

# Set up OCCT external project

# Create a custom target for OCCT build to make dependencies clearer
add_custom_target(occt_libs)

ExternalProject_Add(
    occt_download
    URL https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V7_9_0.zip
    SOURCE_DIR "${OCCT_SOURCE_DIR}"
    BINARY_DIR "${OCCT_BINARY_DIR}"
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
    LOG_DOWNLOAD ON
    LOG_CONFIGURE ON
    LOG_BUILD ON
    LOG_INSTALL ON
    DOWNLOAD_NO_PROGRESS ON
    BUILD_COMMAND ${CMAKE_COMMAND} --build . --config Release -j 2
)

# Set up the dependency chain
add_dependencies(occt_libs occt_download)
add_dependencies(external_downloads occt_download)

# Find Python and nanobind
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module Development.SABIModule)

find_package(nanobind CONFIG REQUIRED)
find_package(Threads REQUIRED)

# Add include directories
include_directories(
  ${CMAKE_CURRENT_SOURCE_DIR}/src
  ${EIGEN_INCLUDE_DIR}
  ${OCCT_INSTALL_DIR}/include
  ${OCCT_INSTALL_DIR}/include/opencascade
)

# Detect OS-specific library paths for OCCT
if(APPLE)
  # Mac OS - check for mac64/clang/lib structure first (common in OCCT builds)
  if(EXISTS "${OCCT_BINARY_DIR}/mac64/clang/lib")
    set(OCCT_LIB_DIR "${OCCT_BINARY_DIR}/mac64/clang/lib")
    message(STATUS "Found OCCT libraries in build directory mac64/clang/lib")
  elseif(EXISTS "${OCCT_INSTALL_DIR}/mac64/clang/lib")
    set(OCCT_LIB_DIR "${OCCT_INSTALL_DIR}/mac64/clang/lib")
    message(STATUS "Found OCCT libraries in mac64/clang/lib")
  else()
    set(OCCT_LIB_DIR "${OCCT_INSTALL_DIR}/lib")
    message(STATUS "Using standard OCCT lib directory")
  endif()
elseif(WIN32)
  # Windows
  if(EXISTS "${OCCT_INSTALL_DIR}/win64/vc14/lib")
    set(OCCT_LIB_DIR "${OCCT_INSTALL_DIR}/win64/vc14/lib")
  else()
    set(OCCT_LIB_DIR "${OCCT_INSTALL_DIR}/lib")
  endif()
else()
  # Linux
  if(EXISTS "${OCCT_INSTALL_DIR}/lin64/gcc/lib")
    set(OCCT_LIB_DIR "${OCCT_INSTALL_DIR}/lin64/gcc/lib")
  else()
    set(OCCT_LIB_DIR "${OCCT_INSTALL_DIR}/lib")
  endif()
endif()

message(STATUS "OCCT library directory: ${OCCT_LIB_DIR}")

# Set up link directories 
link_directories(
  ${OCCT_LIB_DIR}
)

# Define a function to add a nanobind module with common settings
function(add_nanobind_extension name source)
  # Delay the module creation until after OCCT has been built
  add_custom_command(
    OUTPUT ${name}_sentinel
    COMMAND ${CMAKE_COMMAND} -E touch ${name}_sentinel
    DEPENDS occt_download
    COMMENT "Ensuring OCCT libraries are built for ${name}"
  )
  add_custom_target(${name}_ensure_occt DEPENDS ${name}_sentinel)

  # Now create the module after ensuring OCCT is built
  nanobind_add_module(
    ${name}
    STABLE_ABI
    NB_STATIC
    ${source}
  )
  add_dependencies(${name} ${name}_ensure_occt)
  
  # Apply precompiled headers
  target_precompile_headers(${name} PRIVATE src/compas.h)
  
  # Include directories
  target_include_directories(${name} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${EIGEN_INCLUDE_DIR}
    ${nanobind_INCLUDE_DIRS}
  )
  
  # Add OCCT includes - try both source and install locations
  target_include_directories(${name} PRIVATE
    ${OCCT_SOURCE_DIR}/inc
    ${OCCT_BINARY_DIR}/inc
    ${OCCT_INSTALL_DIR}/include
    ${OCCT_INSTALL_DIR}/include/opencascade
  )
  
  # Add dependencies
  add_dependencies(${name} external_downloads)
  add_dependencies(${name} occt_libs)
  
  # Hard-coded platform-specific library path based on what we know about OCCT
  if(APPLE)
    set(OCCT_ACTUAL_LIB_DIR "${OCCT_BINARY_DIR}/mac64/clang/lib")
  elseif(WIN32)
    set(OCCT_ACTUAL_LIB_DIR "${OCCT_BINARY_DIR}/win64/vc14/lib")
  else() # Linux
    set(OCCT_ACTUAL_LIB_DIR "${OCCT_BINARY_DIR}/lin64/gcc/lib")
  endif()
  
  message(STATUS "Using OCCT lib dir: ${OCCT_ACTUAL_LIB_DIR}")
  
  # Now force-add all the libraries OCCT needs
  # This is a more direct approach when find_library is not working reliably
  target_link_libraries(${name} PRIVATE
    ${OCCT_ACTUAL_LIB_DIR}/libTKernel.a
    ${OCCT_ACTUAL_LIB_DIR}/libTKMath.a
    ${OCCT_ACTUAL_LIB_DIR}/libTKG2d.a
    ${OCCT_ACTUAL_LIB_DIR}/libTKG3d.a
    ${OCCT_ACTUAL_LIB_DIR}/libTKGeomBase.a
    ${OCCT_ACTUAL_LIB_DIR}/libTKBRep.a
    ${OCCT_ACTUAL_LIB_DIR}/libTKGeomAlgo.a
    ${OCCT_ACTUAL_LIB_DIR}/libTKTopAlgo.a
    ${OCCT_ACTUAL_LIB_DIR}/libTKShHealing.a
    ${OCCT_ACTUAL_LIB_DIR}/libTKPrim.a
    ${OCCT_ACTUAL_LIB_DIR}/libTKBO.a
    ${OCCT_ACTUAL_LIB_DIR}/libTKMesh.a
    ${OCCT_ACTUAL_LIB_DIR}/libTKLCAF.a
  )
  
  # Install the module
  install(TARGETS ${name} LIBRARY DESTINATION compas_occt)
endfunction()

# Create individual extension modules for each C++ file
# Copy this line with new file name and module name
add_nanobind_extension(_primitives src/primitives.cpp)
add_nanobind_extension(_curves src/compas_occt/_curves.cpp)

message(STATUS "============= Build Configuration =============")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Standard: C++${CMAKE_CXX_STANDARD}")
message(STATUS "Eigen Include Dir: ${EIGEN_INCLUDE_DIR}")
message(STATUS "OCCT Source Dir: ${OCCT_SOURCE_DIR}")
message(STATUS "OCCT Install Dir: ${OCCT_INSTALL_DIR}")
message(STATUS "OCCT Library Dir: ${OCCT_LIB_DIR}")

# Force OCCT libraries to be built before nanobind modules
set_directory_properties(PROPERTIES ADDITIONAL_MAKE_CLEAN_FILES "${OCCT_BINARY_DIR};${OCCT_INSTALL_DIR}")
message(STATUS "=======================================")