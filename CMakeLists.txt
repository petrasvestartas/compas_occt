# =============================================================================
# BASIC PROJECT SETUP
# =============================================================================
cmake_minimum_required(VERSION 3.15)
project(compas_occt LANGUAGES CXX)

# Build configuration with C++20 in Release mode
set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
set(CMAKE_CXX_STANDARD 20 CACHE STRING "C++ standard to use for the build." FORCE)
set(CMAKE_CXX_STANDARD_REQUIRED ON CACHE BOOL "Require the specified C++ standard." FORCE)
set(CMAKE_CXX_EXTENSIONS OFF CACHE BOOL "Disable compiler-specific extensions." FORCE)

# Platform-specific configurations
if(APPLE)
  # Detect and set native architecture for macOS (arm64 or x86_64)
  execute_process(COMMAND uname -m OUTPUT_VARIABLE HOST_ARCH OUTPUT_STRIP_TRAILING_WHITESPACE)
  set(CMAKE_OSX_ARCHITECTURES "${HOST_ARCH}" CACHE STRING "Build architecture for macOS" FORCE)
  set(CMAKE_OSX_DEPLOYMENT_TARGET "11.00" CACHE STRING "Minimum macOS deployment version" FORCE)
  message(STATUS "Building for macOS with ${HOST_ARCH} architecture")
elseif(WIN32 AND MSVC)
  # Windows-specific definitions
  add_definitions(-D_WIN32_WINNT=0x0601 -D_CRT_SECURE_NO_WARNINGS)
elseif(CMAKE_COMPILER_IS_GNUCXX)
  # For Python compatibility on Linux
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D_GLIBCXX_USE_CXX11_ABI=0")
endif()

# Required packages
include(ExternalProject)
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module Development.SABIModule)
find_package(nanobind CONFIG REQUIRED)

# Thread support
set(CMAKE_THREAD_PREFER_PTHREAD TRUE)
set(THREADS_PREFER_PTHREAD_FLAG TRUE)
find_package(Threads REQUIRED)
if(NOT Threads_FOUND)
  message(FATAL_ERROR "Required dependency 'Threads' not found")
endif()

# =============================================================================
# EXTERNAL DEPENDENCIES
# =============================================================================

# Configure paths
set(EXTERNAL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external")
set(CMAKE_MODULE_PATH "${CMAKE_MODULE_PATH};${CMAKE_CURRENT_SOURCE_DIR}/cmake")

# Eigen (header-only library)
set(EIGEN_INCLUDE_DIR "${EXTERNAL_DIR}/eigen")
set(EIGEN_DOWNLOAD_NEEDED NOT EXISTS "${EIGEN_INCLUDE_DIR}/Eigen/Core")
if(EIGEN_DOWNLOAD_NEEDED)
  message(STATUS "Eigen headers not found. Will download.")
else()
  message(STATUS "Using existing Eigen installation at: ${EIGEN_INCLUDE_DIR}")
endif()

# OCCT library paths
set(OCCT_DIR "${EXTERNAL_DIR}/occt")
set(OCCT_BUILD_DIR "${CMAKE_CURRENT_BINARY_DIR}/occt_build")
set(OCCT_INSTALL_DIR "${CMAKE_CURRENT_BINARY_DIR}/occt_install")
set(OCCT_KERNEL_LIBRARY "${OCCT_INSTALL_DIR}/lib/libTKernel${CMAKE_STATIC_LIBRARY_SUFFIX}")
set(OCCT_DOWNLOAD_NEEDED NOT EXISTS "${OCCT_KERNEL_LIBRARY}")

# Check if OCCT kernel library exists as indicator for complete installation
if(NOT EXISTS "${OCCT_KERNEL_LIBRARY}")
  message(STATUS "OCCT library not found. Will download and build.")
  set(OCCT_DOWNLOAD_NEEDED TRUE)
else()
  message(STATUS "Using existing OCCT installation at: ${OCCT_INSTALL_DIR}")
endif()

# Define the list of OCCT modules we need
set(OCCT_MODULES
  "TKernel"
  "TKMath"
  "TKG2d"
  "TKG3d"
  "TKGeomBase"
  "TKBRep"
  "TKGeomAlgo"
  "TKTopAlgo"
  "TKShHealing"
  "TKMesh"
  "TKBO"
  "TKPrim"
  "TKFeat"
  "TKOffset"
  "TKFillet"
  "TKHLR"
  "TKBool"
)

# Helper function to get OCCT library paths
function(define_occt_library_paths)
  if(WIN32)
    # Windows format using actual build location
    set(OCCT_LIB_DIR "${OCCT_BUILD_DIR}/win64/vc14/lib" PARENT_SCOPE)
    set(OCCT_LIB_PREFIX "" PARENT_SCOPE)
  else()
    # Unix format (with 'lib' prefix)
    set(OCCT_LIB_DIR "${OCCT_INSTALL_DIR}/lib" PARENT_SCOPE)
    set(OCCT_LIB_PREFIX "lib" PARENT_SCOPE)
  endif()
  
  # Define each library variable
  foreach(MODULE ${OCCT_MODULES})
    if(WIN32)
      set(OCCT_LIBRARY_${MODULE} "${OCCT_BUILD_DIR}/win64/vc14/lib/${MODULE}${CMAKE_STATIC_LIBRARY_SUFFIX}" PARENT_SCOPE)
    else()
      set(OCCT_LIBRARY_${MODULE} "${OCCT_INSTALL_DIR}/lib/lib${MODULE}${CMAKE_STATIC_LIBRARY_SUFFIX}" PARENT_SCOPE)
    endif()
  endforeach()
endfunction()

# Call function to define all library paths
define_occt_library_paths()

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
  # Configure OCCT build with minimal required components and platform-specific settings
  set(OCCT_CMAKE_ARGS
    # Common settings for all platforms
    -DCMAKE_INSTALL_PREFIX=${OCCT_INSTALL_DIR}
    -DCMAKE_BUILD_TYPE=Release
    -DBUILD_LIBRARY_TYPE=Static
    -DBUILD_USE_PCH=OFF
    -DBUILD_OPT_PROFILE=Production
    # Disable unneeded components to reduce build size/time
    -DUSE_TK=OFF -DUSE_VTK=OFF -DUSE_FREETYPE=OFF -DUSE_OPENGL=OFF
    -DBUILD_SAMPLES_MFC=OFF -DBUILD_SAMPLES_QT=OFF -DBUILD_Inspector=OFF -DINSTALL_SAMPLES=OFF
    -DBUILD_MODULE_ApplicationFramework=OFF -DBUILD_MODULE_DataExchange=OFF
    -DBUILD_MODULE_Draw=OFF -DBUILD_MODULE_VisualizationTest=OFF -DBUILD_MODULE_Visualization=OFF
  )
  
  # Add platform-specific arguments
  if(APPLE)
    list(APPEND OCCT_CMAKE_ARGS
      # macOS architecture and deployment target
      "-DCMAKE_OSX_ARCHITECTURES=${CMAKE_OSX_ARCHITECTURES}"
      "-DCMAKE_OSX_DEPLOYMENT_TARGET=${CMAKE_OSX_DEPLOYMENT_TARGET}"
      # RPATH settings for better library resolution
      "-DCMAKE_MACOSX_RPATH=ON"
      "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON"
      "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=ON"
      "-DBUILD_DOC_Overview=OFF"
    )
    message(STATUS "Building OCCT for macOS with architecture: ${CMAKE_OSX_ARCHITECTURES}")
  elseif(WIN32)
    list(APPEND OCCT_CMAKE_ARGS
      # Use Ninja generator instead of Visual Studio for OCCT (more reliable)
      "-G" "Ninja"
      # Windows-specific module settings
      "-DBUILD_MODULE_MODELING=ON"
      "-DBUILD_MODULE_OCAF=OFF"
      "-DINSTALL_FREETYPE=OFF"
    )
    message(STATUS "Using Windows-specific OCCT build settings")
  endif()
  
  # Create a variable to collect all byproducts
  set(OCCT_BYPRODUCTS)
  foreach(MODULE ${OCCT_MODULES})
    list(APPEND OCCT_BYPRODUCTS ${OCCT_LIBRARY_${MODULE}})
  endforeach()
  
  # Configure and build OCCT with reduced memory usage (-j 2 prevents OOM errors with BRepApprox)
  ExternalProject_Add(occt_external
    URL https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V7_9_0.zip
    PREFIX "${CMAKE_CURRENT_BINARY_DIR}/occt_prefix"
    SOURCE_DIR "${OCCT_DIR}"
    BINARY_DIR "${OCCT_BUILD_DIR}"
    CMAKE_ARGS ${OCCT_CMAKE_ARGS}
    BUILD_COMMAND ${CMAKE_COMMAND} --build . --config Release -j 2
    INSTALL_COMMAND ${CMAKE_COMMAND} --install . --config Release
    CMAKE_CACHE_ARGS "-DCMAKE_OSX_ARCHITECTURES:STRING=${CMAKE_OSX_ARCHITECTURES}"
    BUILD_BYPRODUCTS ${OCCT_BYPRODUCTS}
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
set_property(TARGET occt_lib PROPERTY IMPORTED_LOCATION "${OCCT_LIBRARY_TKernel}")
add_dependencies(occt_lib occt_external)

# =============================================================================
# SECTION 4: NANOBIND MODULE FUNCTION - Platform-specific linking configuration
# =============================================================================

# Helper macro to link OCCT libraries in the correct order
macro(link_occt_libraries target_name)
  target_link_libraries(${target_name} PRIVATE
    # OCCT libraries in proper dependency order
    # Boolean operations and complex shape handling
    "${OCCT_LIBRARY_TKBool}"
    "${OCCT_LIBRARY_TKFillet}"
    "${OCCT_LIBRARY_TKOffset}"
    "${OCCT_LIBRARY_TKFeat}"
    "${OCCT_LIBRARY_TKPrim}"
    "${OCCT_LIBRARY_TKBO}"
    "${OCCT_LIBRARY_TKMesh}"
    "${OCCT_LIBRARY_TKHLR}"
    "${OCCT_LIBRARY_TKShHealing}"
    
    # Mid-level algorithms and topology
    "${OCCT_LIBRARY_TKTopAlgo}"
    "${OCCT_LIBRARY_TKGeomAlgo}"
    
    # Geometry and representations
    "${OCCT_LIBRARY_TKBRep}"
    "${OCCT_LIBRARY_TKGeomBase}"
    "${OCCT_LIBRARY_TKG3d}"
    "${OCCT_LIBRARY_TKG2d}"
    
    # Core libraries
    "${OCCT_LIBRARY_TKMath}"
    "${OCCT_LIBRARY_TKernel}"
  )
endmacro()

# Compiler definitions now incorporated into set_include_directories

# Configure target with appropriate include paths, compiler options and definitions
function(configure_target_for_occt target_name)
  # Common include directories and OCCT definitions
  target_include_directories(${target_name} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${EIGEN_INCLUDE_DIR}
    ${nanobind_INCLUDE_DIRS}
  )
  
  target_compile_definitions(${target_name} PRIVATE
    HAVE_OCCT HAVE_TKG2d HAVE_TKG3d HAVE_TKGeomBase HAVE_TKBRep
  )
  
  # Platform-specific setup
  if(WIN32)
    # Windows include directories
    target_include_directories(${target_name} PRIVATE "${OCCT_INSTALL_DIR}/inc")
    
    # For MSVC, add include directories as compiler options as well
    if(MSVC)
      # Get all OCCT source directories
      file(GLOB _occt_src_dirs LIST_DIRECTORIES true "${OCCT_DIR}/src/*")
      
      # Add them as both include directories and compiler options
      target_include_directories(${target_name} PRIVATE "${OCCT_DIR}/src" "${OCCT_DIR}/inc" ${_occt_src_dirs})
      target_compile_options(${target_name} PRIVATE "/I${OCCT_DIR}/inc" "/I${OCCT_DIR}/src")
      
      foreach(_dir ${_occt_src_dirs})
        if(IS_DIRECTORY "${_dir}")
          target_compile_options(${target_name} PRIVATE "/I${_dir}")
        endif()
      endforeach()
    endif()
  else()
    # Unix/Linux/macOS setup is simpler
    target_include_directories(${target_name} PRIVATE
      "${OCCT_INSTALL_DIR}/include/opencascade"
      "${OCCT_DIR}/src"
    )
  endif()
  
  # Setup linker options for GCC
  if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    target_link_options(${target_name} PRIVATE "-Wl,--no-as-needed" "-Wl,--start-group")
  endif()
  
  # Link OCCT libraries
  link_occt_libraries(${target_name})
  
  # Close linker group if needed
  if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    target_link_options(${target_name} PRIVATE "-Wl,--end-group")
  endif()
endfunction()

# Windows MSVC options now incorporated into set_include_directories

# Define a function to add a nanobind module with common settings
function(add_nanobind_extension name source)
  # Create the nanobind module
  nanobind_add_module(${name} STABLE_ABI NB_STATIC ${source})
  
  # Apply precompiled headers
  target_precompile_headers(${name} PRIVATE src/compas.h)
  
  # Configure all includes, definitions, and linking in one call
  configure_target_for_occt(${name})
  
  # Install the module
  install(TARGETS ${name} LIBRARY DESTINATION compas_occt)
  
  # Add dependency on all_deps_ready to ensure dependencies are built first
  add_dependencies(${name} all_deps_ready)
endfunction()

# =============================================================================
# SECTION 5: TARGET CREATION - Modules and dependency relationships
# =============================================================================

# Create dependency targets
add_custom_target(all_deps_ready)

# Process download dependencies
if(EIGEN_DOWNLOAD_NEEDED)
  add_dependencies(all_deps_ready eigen_download)
endif()
if(OCCT_DOWNLOAD_NEEDED)
  add_dependencies(all_deps_ready occt_external)
endif()

# Create the modules (dependency on all_deps_ready is handled in the function)
add_nanobind_extension(_primitives src/primitives.cpp)
add_nanobind_extension(_curves src/curves.cpp)

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