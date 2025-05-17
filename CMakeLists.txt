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

# Create a file to track the OCCT build status
set(OCCT_MARKER_FILE "${CMAKE_BINARY_DIR}/occt_built_marker.txt")

# Add the OCCT external project with improved tracking
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
      -DBUILD_MODULE_Draw=OFF
    LOG_DOWNLOAD ON
    LOG_CONFIGURE ON
    LOG_BUILD ON
    LOG_INSTALL ON
    DOWNLOAD_NO_PROGRESS ON
    # Build with fewer parallel jobs to avoid memory issues
    BUILD_COMMAND ${CMAKE_COMMAND} --build . --config Release -j 2
    # Add explicit install step to ensure libraries are installed to expected locations
    INSTALL_COMMAND ${CMAKE_COMMAND} --install . --config Release
    # Run a command after the build to create a marker file
    COMMAND ${CMAKE_COMMAND} -E touch ${OCCT_MARKER_FILE}
)

# Set up the dependency chain
add_dependencies(occt_libs occt_download)

# Create a custom command that checks for the marker file
add_custom_command(
    OUTPUT ${OCCT_MARKER_FILE}
    COMMAND ${CMAKE_COMMAND} -E echo "Waiting for OCCT build to complete..."
    DEPENDS occt_download
)

# Add the marker file as a dependency of the custom target
add_custom_target(ensure_occt_built ALL DEPENDS ${OCCT_MARKER_FILE})
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
    set(OCCT_LIB_PREFIX "lib")
    set(OCCT_LIB_EXT ".a")
  elseif(WIN32)
    set(OCCT_ACTUAL_LIB_DIR "${OCCT_BINARY_DIR}/win64/vc14/lib")
    set(OCCT_LIB_PREFIX "")
    set(OCCT_LIB_EXT ".lib")
  else() # Linux
    set(OCCT_ACTUAL_LIB_DIR "${OCCT_BINARY_DIR}/lin64/gcc/lib")
    set(OCCT_LIB_PREFIX "lib")
    set(OCCT_LIB_EXT ".a")
  endif()
  
  message(STATUS "Using OCCT lib dir: ${OCCT_ACTUAL_LIB_DIR}")
  
  # Create directories if they don't exist (for CI environments)
  if(NOT EXISTS "${OCCT_ACTUAL_LIB_DIR}")
    file(MAKE_DIRECTORY "${OCCT_ACTUAL_LIB_DIR}")
    message(STATUS "Created OCCT library directory: ${OCCT_ACTUAL_LIB_DIR}")
  endif()
  
  # Set the list of required OCCT libraries
  set(OCCT_REQUIRED_LIBS
    TKernel
    TKMath
    TKG2d
    TKG3d
    TKGeomBase
    TKBRep
    TKGeomAlgo
    TKTopAlgo
    TKShHealing
    TKPrim
    TKBO
    TKMesh
    TKLCAF
  )
  
  # First verify that OCCT build is complete by checking if crucial libraries exist
  set(OCCT_BUILD_VERIFICATION_TARGET "${OCCT_ACTUAL_LIB_DIR}/${OCCT_LIB_PREFIX}TKernel${OCCT_LIB_EXT}")
  if(NOT EXISTS "${OCCT_BUILD_VERIFICATION_TARGET}")
    message(STATUS "OCCT verification target not found: ${OCCT_BUILD_VERIFICATION_TARGET}")
    message(STATUS "This is expected on the first build. Ensuring dependency is established.")
    message(STATUS "Explicitly adding dependency to ensure OCCT is built first.")
    
    # Add a stronger dependency chain to ensure OCCT is built before modules
    set_property(TARGET ${name} PROPERTY EXCLUDE_FROM_ALL FALSE)
  endif()
  
  # Now force-add all the libraries OCCT needs with platform-specific naming
  foreach(occt_lib ${OCCT_REQUIRED_LIBS})
    set(lib_path "${OCCT_ACTUAL_LIB_DIR}/${OCCT_LIB_PREFIX}${occt_lib}${OCCT_LIB_EXT}")
    message(STATUS "Adding library: ${lib_path}")
    target_link_libraries(${name} PRIVATE ${lib_path})
  endforeach()
  
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