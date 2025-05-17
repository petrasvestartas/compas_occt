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

# Setup external directories
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

# Set up OCCT external project if needed
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/compas_occt")
  message(STATUS "OCCT support detected, adding OCCT build")
  
  # Simple target for OCCT dependencies
  add_custom_target(occt_libs)
  
  # Only try to build OCCT if not already present
  if(NOT EXISTS "${OCCT_INSTALL_DIR}/include/opencascade")
    message(STATUS "OCCT not found, downloading and building")
    
    # Parse any additional OCCT args from the environment
    if(DEFINED ENV{OCCT_CMAKE_ARGS})
      set(OCCT_EXTRA_CMAKE_ARGS $ENV{OCCT_CMAKE_ARGS})
      message(STATUS "Using extra OCCT CMake args from environment: ${OCCT_EXTRA_CMAKE_ARGS}")
    else()
      set(OCCT_EXTRA_CMAKE_ARGS "")
    endif()

    # Set up standard OCCT build args
    set(OCCT_CMAKE_ARGS
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
      ${OCCT_EXTRA_CMAKE_ARGS}
    )

    ExternalProject_Add(
        occt_download
        URL https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V7_9_0.zip
        SOURCE_DIR "${OCCT_SOURCE_DIR}"
        BINARY_DIR "${OCCT_BINARY_DIR}"
        CMAKE_ARGS ${OCCT_CMAKE_ARGS}
        LOG_DOWNLOAD ON
        LOG_CONFIGURE ON
        LOG_BUILD ON
        LOG_INSTALL ON
        DOWNLOAD_NO_PROGRESS ON
        # Build with fewer parallel jobs to avoid memory issues
        BUILD_COMMAND ${CMAKE_COMMAND} --build . --config Release -j 2
        # Add explicit install step to ensure libraries are installed to expected locations
        INSTALL_COMMAND ${CMAKE_COMMAND} --install . --config Release
    )
    
    # Add to dependencies
    add_dependencies(occt_libs occt_download)
    add_dependencies(external_downloads occt_download)
  else()
    message(STATUS "OCCT already installed")
  endif()
  
  # Set up OCCT include and lib paths
  set(OCCT_INCLUDE_DIR "${OCCT_INSTALL_DIR}/include")
  
  # Detect platform-specific paths
  if(APPLE)
    set(OCCT_LIB_DIR "${OCCT_BINARY_DIR}/mac64/clang/lib")
  elseif(WIN32)
    set(OCCT_LIB_DIR "${OCCT_BINARY_DIR}/win64/vc14/lib")
  else()
    set(OCCT_LIB_DIR "${OCCT_BINARY_DIR}/lin64/gcc/lib")
  endif()

endif()

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
  # Create the module
  nanobind_add_module(
    ${name}
    STABLE_ABI
    NB_STATIC
    ${source}
  )
  
  # Add a direct dependency on external downloads instead of using a sentinel
  add_dependencies(${name} external_downloads)
  if(TARGET occt_libs)
    add_dependencies(${name} occt_libs)
  endif()
  
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
  
  # Find all needed OCCT libraries dynamically so it works in both normal and CI environments
  # List of required OCCT modules
  set(OCCT_MODULES TKernel TKMath TKG2d TKG3d TKGeomBase TKBRep TKGeomAlgo TKTopAlgo TKShHealing TKPrim TKMesh TKBO TKLCAF)
  
  # Set up empty list to collect all found libraries
  set(OCCT_LIBS_FOUND)
  
  foreach(MODULE ${OCCT_MODULES})
    # Look for the library in different possible locations
    foreach(LIB_DIR ${OCCT_LIB_DIR} ${OCCT_ACTUAL_LIB_DIR} ${OCCT_INSTALL_DIR}/lib ${OCCT_BINARY_DIR}/mac64/clang/lib ${OCCT_BINARY_DIR}/lin64/gcc/lib ${OCCT_BINARY_DIR}/win64/vc14/lib)
      # For static libraries
      if(EXISTS "${LIB_DIR}/lib${MODULE}.a")
        list(APPEND OCCT_LIBS_FOUND "${LIB_DIR}/lib${MODULE}.a")
        break()
      # For shared libraries on MacOS
      elseif(APPLE AND EXISTS "${LIB_DIR}/lib${MODULE}.dylib")
        list(APPEND OCCT_LIBS_FOUND "${LIB_DIR}/lib${MODULE}.dylib")
        break()
      # For shared libraries on Linux
      elseif(UNIX AND NOT APPLE AND EXISTS "${LIB_DIR}/lib${MODULE}.so")
        list(APPEND OCCT_LIBS_FOUND "${LIB_DIR}/lib${MODULE}.so")
        break()
      # For shared libraries on Windows
      elseif(WIN32 AND EXISTS "${LIB_DIR}/${MODULE}.lib")
        list(APPEND OCCT_LIBS_FOUND "${LIB_DIR}/${MODULE}.lib")
        break()
      endif()
    endforeach()
  endforeach()
  
  # If we found libraries, link against them
  if(OCCT_LIBS_FOUND)
    message(STATUS "Found OCCT libraries for ${name}:")
    foreach(LIB ${OCCT_LIBS_FOUND})
      message(STATUS "  -- Adding library: ${LIB}")
    endforeach()
    target_link_libraries(${name} PRIVATE ${OCCT_LIBS_FOUND})
  else()
    message(WARNING "Could not find OCCT libraries for ${name}!")
  endif()
  
  # Library linking is handled by dynamic library finding above
  
  # Install the module
  install(TARGETS ${name} LIBRARY DESTINATION compas_occt)
endfunction()

# Create individual extension modules for each C++ file
# Primary module - always built
add_nanobind_extension(_primitives src/primitives.cpp)

# Check if we're running in a CI environment
if(DEFINED ENV{CI} OR DEFINED ENV{CIBUILDWHEEL})
  message(STATUS "CI environment detected - skipping advanced modules")
  # Skip building the _curves module in CI environment to focus on core functionality
else()
  # Advanced OCCT modules - only built locally
  message(STATUS "Building advanced modules including _curves")
  add_nanobind_extension(_curves src/compas_occt/_curves.cpp)
  
  # Special handling for _curves module which needs more OCCT components
  if(TARGET _curves)
    # Add additional OCCT libraries
    target_link_libraries(_curves PRIVATE
      ${CMAKE_DL_LIBS}  # Add dynamic loading libraries which are often needed
    )
    
    # On macOS, also add system frameworks that OCCT might need
    if(APPLE)
      find_library(COCOA_LIBRARY Cocoa)
      find_library(IOKIT_LIBRARY IOKit)
      target_link_libraries(_curves PRIVATE ${COCOA_LIBRARY} ${IOKIT_LIBRARY})
    endif()
  endif()
endif()

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