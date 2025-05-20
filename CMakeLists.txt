# =============================================================================
# SECTION 1: INITIAL SETUP - Basic project configuration and build settings
# =============================================================================

cmake_minimum_required(VERSION 3.15)
project(compas_occt LANGUAGES CXX)

# Build configuration
set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
set(CMAKE_CXX_STANDARD 20 CACHE STRING "C++ standard to use for the build." FORCE)
set(CMAKE_CXX_STANDARD_REQUIRED ON CACHE BOOL "Require the specified C++ standard." FORCE)
set(CMAKE_CXX_EXTENSIONS OFF CACHE BOOL "Disable compiler-specific extensions." FORCE)

# Configure macOS architecture - build for native architecture only for better compatibility
if(APPLE)
  # Detect host architecture
  execute_process(
    COMMAND uname -m
    OUTPUT_VARIABLE HOST_ARCH
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )
  
  # Set architecture based on host (one or the other, not universal binary)
  if(HOST_ARCH STREQUAL "arm64")
    set(CMAKE_OSX_ARCHITECTURES "arm64" CACHE STRING "Build architecture for macOS" FORCE)
    message(STATUS "Building for Apple Silicon (arm64)")
  else()
    set(CMAKE_OSX_ARCHITECTURES "x86_64" CACHE STRING "Build architecture for macOS" FORCE)
    message(STATUS "Building for Intel Mac (x86_64)")
  endif()
  
  # Set minimum macOS version
  set(CMAKE_OSX_DEPLOYMENT_TARGET "11.00" CACHE STRING "Minimum macOS deployment version" FORCE)
endif()

# For Python compatibility, ensure ABI compatibility with libstdc++
if(CMAKE_COMPILER_IS_GNUCXX)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D_GLIBCXX_USE_CXX11_ABI=0")
endif()

include(ExternalProject)

# Find Python first (required for nanobind)
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module Development.SABIModule)

# Then include nanobind for Python bindings
find_package(nanobind CONFIG REQUIRED)

# Improved pthread handling
set(CMAKE_THREAD_PREFER_PTHREAD TRUE)
set(THREADS_PREFER_PTHREAD_FLAG TRUE)
find_package(Threads REQUIRED)
if(NOT Threads_FOUND)
  message(FATAL_ERROR "Required dependency 'Threads' not found")
endif()

# Add special handling for Windows
if(WIN32)
  add_definitions(-D_WIN32_WINNT=0x0601)
  if(MSVC)
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
  endif()
endif()

# =============================================================================
# SECTION 2: EXTERNAL DEPENDENCIES CONFIGURATION - Paths and dependency checks
# =============================================================================

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

# We're skipping template static library as it's not needed

# -------------------- OCCT library --------------------------
set(OCCT_DIR "${EXTERNAL_DIR}/occt")
set(OCCT_BUILD_DIR "${CMAKE_CURRENT_BINARY_DIR}/occt_build")
set(OCCT_INSTALL_DIR "${CMAKE_CURRENT_BINARY_DIR}/occt_install")
# Set OCCT include paths in a cross-platform compatible way
# For Windows, include all OCCT source directories recursively
if(WIN32)
  # Start with base include paths
  set(OCCT_INCLUDE_DIR
    "${OCCT_INSTALL_DIR}/include/opencascade"
    "${OCCT_INSTALL_DIR}/include"
    "${OCCT_DIR}/src"
    "${OCCT_DIR}/inc"
  )
  
  # Get a list of all subdirectories in the OCCT source directory
  file(GLOB OCCT_SRC_SUBDIRS LIST_DIRECTORIES true "${OCCT_DIR}/src/*")
  foreach(DIR ${OCCT_SRC_SUBDIRS})
    if(IS_DIRECTORY "${DIR}")
      list(APPEND OCCT_INCLUDE_DIR "${DIR}")
    endif()
  endforeach()
else()
  set(OCCT_INCLUDE_DIR 
    "${OCCT_INSTALL_DIR}/include/opencascade"
    "${OCCT_INSTALL_DIR}/include"
    "${OCCT_DIR}/src"
  )
endif()
set(OCCT_KERNEL_LIBRARY "${OCCT_INSTALL_DIR}/lib/libTKernel${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_DOWNLOAD_NEEDED FALSE)

# Check if OCCT kernel library exists as indicator for complete installation
if(NOT EXISTS "${OCCT_KERNEL_LIBRARY}")
  message(STATUS "OCCT library not found. Will download and build.")
  set(OCCT_DOWNLOAD_NEEDED TRUE)
else()
  message(STATUS "Using existing OCCT installation at: ${OCCT_INSTALL_DIR}")
endif()

# Define OCCT library paths with proper platform-specific path handling
if(WIN32)
  # Windows format using actual build location
  set(OCCT_WIN_LIB_DIR "${OCCT_BUILD_DIR}/win64/vc14/lib")
  
  set(OCCT_LIBRARY_KERNEL "${OCCT_WIN_LIB_DIR}/TKernel${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_MATH "${OCCT_WIN_LIB_DIR}/TKMath${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_G2D "${OCCT_WIN_LIB_DIR}/TKG2d${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_G3D "${OCCT_WIN_LIB_DIR}/TKG3d${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_GEOMBASE "${OCCT_WIN_LIB_DIR}/TKGeomBase${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_BREP "${OCCT_WIN_LIB_DIR}/TKBRep${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_GEOMALGO "${OCCT_WIN_LIB_DIR}/TKGeomAlgo${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_TOPALGO "${OCCT_WIN_LIB_DIR}/TKTopAlgo${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_SHHEALING "${OCCT_WIN_LIB_DIR}/TKShHealing${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_MESH "${OCCT_WIN_LIB_DIR}/TKMesh${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_BO "${OCCT_WIN_LIB_DIR}/TKBO${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_PRIM "${OCCT_WIN_LIB_DIR}/TKPrim${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_FEAT "${OCCT_WIN_LIB_DIR}/TKFeat${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_OFFSET "${OCCT_WIN_LIB_DIR}/TKOffset${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_FILLET "${OCCT_WIN_LIB_DIR}/TKFillet${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_HLR "${OCCT_WIN_LIB_DIR}/TKHLR${CMAKE_STATIC_LIBRARY_SUFFIX}")
  set(OCCT_LIBRARY_BOOL "${OCCT_WIN_LIB_DIR}/TKBool${CMAKE_STATIC_LIBRARY_SUFFIX}")
else()
  # Unix format (with 'lib' prefix)
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
endif()

# Create a main target to manage all external dependencies
add_custom_target(external_downloads ALL)

# Create a target to ensure OCCT libraries are ready
add_custom_target(occt_libraries_built
  COMMENT "Ensuring OCCT libraries are ready"
)

# =============================================================================
# SECTION 3: BUILD TARGETS FOR DEPENDENCIES - ExternalProject setup
# =============================================================================

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

# We're removing template static library setup as requested

# 3. OCCT setup
if(OCCT_DOWNLOAD_NEEDED)
  message(STATUS "Setting up OCCT build...")
  # Prepare OCCT CMake arguments
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
      -DBUILD_MODULE_Visualization=OFF
      -DUSE_OPENGL=OFF
  )
  
  # Add platform-specific arguments
  if(APPLE)
    # Pass the native architecture flag to OCCT
    list(APPEND OCCT_CMAKE_ARGS
      "-DCMAKE_OSX_ARCHITECTURES=${CMAKE_OSX_ARCHITECTURES}"
      "-DCMAKE_OSX_DEPLOYMENT_TARGET=${CMAKE_OSX_DEPLOYMENT_TARGET}"
    )
    
    # Additional macOS-specific settings for better compatibility
    list(APPEND OCCT_CMAKE_ARGS
      "-DBUILD_MODULE_Draw=OFF"
      "-DBUILD_DOC_Overview=OFF"
      "-DBUILD_LIBRARY_TYPE=Static"
      "-DCMAKE_MACOSX_RPATH=ON"
      "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON"
      "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=ON"
    )
    
    message(STATUS "Building OCCT for macOS with architecture: ${CMAKE_OSX_ARCHITECTURES}")
  endif()
  
  # Windows-specific settings to improve build reliability
  if(WIN32)
    list(APPEND OCCT_CMAKE_ARGS
      # Use Ninja generator instead of Visual Studio for OCCT (more reliable)
      "-G" "Ninja"
      # Disable some problematic OCCT modules that often cause Windows build issues
      "-DBUILD_MODULE_VISUALIZATION=OFF"
      "-DBUILD_MODULE_MODELING=ON"
      "-DBUILD_MODULE_OCAF=OFF"
      "-DINSTALL_FREETYPE=OFF"
    )
    message(STATUS "Using Windows-specific OCCT build settings")
  endif()
  
  ExternalProject_Add(
    occt_external
    URL https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V7_9_0.zip
    PREFIX "${CMAKE_CURRENT_BINARY_DIR}/occt_prefix"
    SOURCE_DIR "${OCCT_DIR}"
    BINARY_DIR "${OCCT_BUILD_DIR}"
    CMAKE_ARGS ${OCCT_CMAKE_ARGS}
    # Limit to 2 parallel jobs to avoid memory issues
    BUILD_COMMAND ${CMAKE_COMMAND} --build . --config Release -j 2
    INSTALL_COMMAND ${CMAKE_COMMAND} --install . --config Release
    CMAKE_CACHE_ARGS
      "-DCMAKE_OSX_ARCHITECTURES:STRING=${CMAKE_OSX_ARCHITECTURES}"
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
add_library(occt_lib STATIC IMPORTED GLOBAL)
set_property(TARGET occt_lib PROPERTY IMPORTED_LOCATION "${OCCT_KERNEL_LIBRARY}")
add_dependencies(occt_lib occt_external)

# =============================================================================
# SECTION 4: NANOBIND MODULE FUNCTION - Platform-specific linking configuration
# =============================================================================

# Helper macro to link OCCT libraries in the correct order
macro(link_occt_libraries target_name)
  target_link_libraries(${target_name} PRIVATE
    # OCCT libraries in proper dependency order
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
endmacro()

# Helper macro to set common OCCT compiler definitions
macro(set_occt_compiler_definitions target_name)
  target_compile_definitions(${target_name} PRIVATE
    HAVE_OCCT
    HAVE_TKG2d
    HAVE_TKG3d
    HAVE_TKGeomBase
    HAVE_TKBRep
  )
endmacro()

# Helper macro to set up include directories based on platform
macro(set_include_directories target_name)
  # Common include directories for all platforms
  target_include_directories(${target_name} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${EIGEN_INCLUDE_DIR}
    ${nanobind_INCLUDE_DIRS}
  )
  
  # Platform-specific OCCT include directory
  if(WIN32)
    # Windows uses a different include path structure
    target_include_directories(${target_name} PRIVATE "${OCCT_INSTALL_DIR}/inc")
    message(STATUS "Using simplified OCCT include path for ${target_name}: ${OCCT_INSTALL_DIR}/inc")
  else()
    # Unix/Linux/macOS path
    target_include_directories(${target_name} PRIVATE "${OCCT_INSTALL_DIR}/include/opencascade")
  endif()
endmacro()

# Helper macro to add Windows-specific compiler options
macro(add_msvc_compiler_options target_name)
  if(WIN32 AND MSVC)
    # Add base OCCT directories via compiler options
    target_compile_options(${target_name} PRIVATE
      "/I${OCCT_DIR}/inc"
      "/I${OCCT_DIR}/src"
    )
    
    # Add ALL OCCT source subdirectories as include paths via compiler options
    file(GLOB _occt_src_dirs LIST_DIRECTORIES true "${OCCT_DIR}/src/*")
    foreach(_dir ${_occt_src_dirs})
      if(IS_DIRECTORY "${_dir}")
        target_compile_options(${target_name} PRIVATE "/I${_dir}")
      endif()
    endforeach()
  endif()
endmacro()

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
  
  # Set up include directories with platform-specific handling
  set_include_directories(${name})
  
  # Link OCCT libraries using our helper macro (works for both Windows and Unix/Linux)
  link_occt_libraries(${name})
  
  # Add common OCCT compiler definitions
  set_occt_compiler_definitions(${name})
  
  # Add Windows-specific compiler options for MSVC
  add_msvc_compiler_options(${name})
  
  # For GCC/Linux, start the group to handle circular dependencies
  if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    target_link_options(${name} PRIVATE "-Wl,--no-as-needed" "-Wl,--start-group")
  endif()
  
  # Link OCCT libraries using our helper macro (works for both Windows and Unix/Linux)
  link_occt_libraries(${name})
  
  # For GCC/Linux, end the group to handle circular dependencies
  if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    target_link_options(${name} PRIVATE "-Wl,--end-group")
  endif()
  
  # Install the module
  install(TARGETS ${name} LIBRARY DESTINATION compas_occt)
endfunction()

# =============================================================================
# SECTION 5: TARGET CREATION - Modules and dependency relationships
# =============================================================================

# Create a target that requires all external libraries to be built first
add_custom_target(all_deps_ready)

# Add dependencies to this target based on what needs downloading
if(EIGEN_DOWNLOAD_NEEDED)
  add_dependencies(all_deps_ready eigen_download)
endif()

if(OCCT_DOWNLOAD_NEEDED)
  add_dependencies(all_deps_ready occt_external)
endif()

# Create the modules and ensure they depend on all dependencies being ready
add_nanobind_extension(_primitives src/primitives.cpp)
add_nanobind_extension(_curves src/curves.cpp)

# Make sure OCCT is fully built before trying to build our modules
add_dependencies(_primitives all_deps_ready)
add_dependencies(_curves all_deps_ready)

# =============================================================================
# SECTION 6: BUILD INFORMATION - Display configuration settings
# =============================================================================

# Display build configuration information
message(STATUS "============= Build Configuration =============")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Standard: C++${CMAKE_CXX_STANDARD}")
message(STATUS "Eigen Include Dir: ${EIGEN_INCLUDE_DIR}")
message(STATUS "OCCT Install Dir: ${OCCT_INSTALL_DIR}")
message(STATUS "=======================================")