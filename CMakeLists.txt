# =============================================================================
# BASIC PROJECT SETUP
# =============================================================================
cmake_minimum_required(VERSION 3.15)
project(compas_occt LANGUAGES CXX)

# Build configuration with C++20 in Release mode
set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
set(CMAKE_CXX_STANDARD 20 CACHE STRING "C++ standard to use for the build." FORCE)
set(CMAKE_CXX_STANDARD_REQUIRED ON CACHE BOOL "Require the specified C++ standard." FORCE)

# Platform-specific configurations - simplified since cibuildwheels handles architectures separately
if(APPLE)
  # Set minimum macOS version - architecture is now determined by the build environment
  set(CMAKE_OSX_DEPLOYMENT_TARGET "11.00" CACHE STRING "Minimum macOS deployment version" FORCE)
elseif(WIN32)
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
find_package(Threads REQUIRED)

# =============================================================================
# EXTERNAL DEPENDENCIES
# =============================================================================

# Configure paths
set(EXTERNAL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external")

# Set up external libraries with simplified dependency checks
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
if(OCCT_DOWNLOAD_NEEDED)
  message(STATUS "OCCT library not found. Will download and build.")
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
    set(OCCT_LIB_PATTERN "${OCCT_BUILD_DIR}/win64/vc14/lib/%s${CMAKE_STATIC_LIBRARY_SUFFIX}")
  else()
    set(OCCT_LIB_PATTERN "${OCCT_INSTALL_DIR}/lib/lib%s${CMAKE_STATIC_LIBRARY_SUFFIX}")
  endif()
  
  # Define each library variable using the pattern
  foreach(MODULE ${OCCT_MODULES})
    string(REPLACE "%s" "${MODULE}" LIB_PATH "${OCCT_LIB_PATTERN}")
    set(OCCT_LIBRARY_${MODULE} "${LIB_PATH}" PARENT_SCOPE)
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
# SECTION 3: EXTERNAL DEPENDENCIES
# =============================================================================

# 1. Download Eigen if needed
if(EIGEN_DOWNLOAD_NEEDED)
  message(STATUS "Downloading Eigen...")
  ExternalProject_Add(eigen_download
    URL https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip
    SOURCE_DIR "${EIGEN_INCLUDE_DIR}"
    CONFIGURE_COMMAND "" BUILD_COMMAND "" INSTALL_COMMAND ""
    LOG_DOWNLOAD ON UPDATE_COMMAND "" PATCH_COMMAND ""
    TLS_VERIFY ON
  )
  add_dependencies(external_downloads eigen_download)
endif()

# We're removing template static library setup as requested

# 3. OCCT setup
if(OCCT_DOWNLOAD_NEEDED)
  message(STATUS "Setting up OCCT build...")
  # Common OCCT cmake args for all platforms
  set(OCCT_CMAKE_ARGS
    # Basic settings and memory optimizations
    -DCMAKE_INSTALL_PREFIX=${OCCT_INSTALL_DIR}
    -DCMAKE_BUILD_TYPE=Release
    -DBUILD_LIBRARY_TYPE=Static
    -DBUILD_USE_PCH=OFF                    # Critical for memory usage
    -DBUILD_OPT_PROFILE=Production         # Reduces memory consumption
    -DBUILD_RELEASE_DISABLE_EXCEPTIONS=OFF
    
    # Disable all unnecessary features
    -DUSE_TK=OFF -DUSE_VTK=OFF -DUSE_FREETYPE=OFF -DUSE_OPENGL=OFF
    -DBUILD_SAMPLES_MFC=OFF -DBUILD_SAMPLES_QT=OFF -DBUILD_Inspector=OFF -DINSTALL_SAMPLES=OFF
    -DBUILD_MODULE_ApplicationFramework=OFF -DBUILD_MODULE_DataExchange=OFF
    -DBUILD_MODULE_Draw=OFF -DBUILD_MODULE_VisualizationTest=OFF -DBUILD_MODULE_Visualization=OFF
  )
  
  # Platform-specific args
  if(APPLE)
    list(APPEND OCCT_CMAKE_ARGS
      "-DCMAKE_OSX_DEPLOYMENT_TARGET=${CMAKE_OSX_DEPLOYMENT_TARGET}"
      "-DCMAKE_MACOSX_RPATH=ON"
      "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON"
      "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=ON"
      "-DBUILD_DOC_Overview=OFF"
    )
  elseif(WIN32)
    list(APPEND OCCT_CMAKE_ARGS
      "-G" "Ninja" "-DBUILD_MODULE_MODELING=ON" "-DBUILD_MODULE_OCAF=OFF" "-DINSTALL_FREETYPE=OFF"
    )
  endif()
  
  # Collect all library byproducts in one line
  set(OCCT_BYPRODUCTS)
  foreach(MODULE ${OCCT_MODULES})
    list(APPEND OCCT_BYPRODUCTS ${OCCT_LIBRARY_${MODULE}})
  endforeach()
  
  # Configure and build OCCT (with -j 2 to prevent memory issues with BRepApprox components)
  ExternalProject_Add(occt_external
    URL https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V7_9_0.zip
    PREFIX "${CMAKE_CURRENT_BINARY_DIR}/occt_prefix"
    SOURCE_DIR "${OCCT_DIR}" BINARY_DIR "${OCCT_BUILD_DIR}"
    CMAKE_ARGS ${OCCT_CMAKE_ARGS}
    BUILD_COMMAND ${CMAKE_COMMAND} --build . --config Release -j 2
    INSTALL_COMMAND ${CMAKE_COMMAND} --install . --config Release
    CMAKE_CACHE_ARGS "-DCMAKE_OSX_ARCHITECTURES:STRING=${CMAKE_OSX_ARCHITECTURES}"
    BUILD_BYPRODUCTS ${OCCT_BYPRODUCTS}
    LOG_DOWNLOAD ON LOG_CONFIGURE ON LOG_BUILD ON LOG_INSTALL ON
    UPDATE_COMMAND "" UPDATE_DISCONNECTED ON
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

# Link OCCT libraries in dependency order
function(link_occt_libraries target_name)
  # Direct list of libraries in the required order
  target_link_libraries(${target_name} PRIVATE
    # Boolean operations and complex shape handling
    "${OCCT_LIBRARY_TKBool}" "${OCCT_LIBRARY_TKFillet}" "${OCCT_LIBRARY_TKOffset}"
    "${OCCT_LIBRARY_TKFeat}" "${OCCT_LIBRARY_TKPrim}" "${OCCT_LIBRARY_TKBO}"
    "${OCCT_LIBRARY_TKMesh}" "${OCCT_LIBRARY_TKHLR}" "${OCCT_LIBRARY_TKShHealing}"
    # Algorithms and topology
    "${OCCT_LIBRARY_TKTopAlgo}" "${OCCT_LIBRARY_TKGeomAlgo}"
    # Geometry
    "${OCCT_LIBRARY_TKBRep}" "${OCCT_LIBRARY_TKGeomBase}"
    "${OCCT_LIBRARY_TKG3d}" "${OCCT_LIBRARY_TKG2d}"
    # Core
    "${OCCT_LIBRARY_TKMath}" "${OCCT_LIBRARY_TKernel}"
  )
endfunction()

# Compiler definitions now incorporated into set_include_directories

# Configure target with appropriate include paths, compiler options and link libraries
function(configure_target_for_occt target_name)
  # ---- 1. Set up include directories ----
  # Common include directories for all platforms
  set(COMMON_INCLUDES
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${EIGEN_INCLUDE_DIR}
    ${nanobind_INCLUDE_DIRS}
  )
  
  # Platform-specific includes
  if(WIN32)
    set(PLATFORM_INCLUDES "${OCCT_INSTALL_DIR}/inc")
    if(MSVC)
      file(GLOB OCCT_SRC_DIRS LIST_DIRECTORIES true "${OCCT_DIR}/src/*")
      list(APPEND PLATFORM_INCLUDES "${OCCT_DIR}/src" "${OCCT_DIR}/inc" ${OCCT_SRC_DIRS})
      
      # Add MSVC include directory options directly
      foreach(DIR "${OCCT_DIR}/inc" "${OCCT_DIR}/src" ${OCCT_SRC_DIRS})
        if(IS_DIRECTORY "${DIR}")
          target_compile_options(${target_name} PRIVATE "/I${DIR}")
        endif()
      endforeach()
    endif()
  else()
    set(PLATFORM_INCLUDES "${OCCT_INSTALL_DIR}/include/opencascade" "${OCCT_DIR}/src")
  endif()
  
  # Apply all include directories
  target_include_directories(${target_name} PRIVATE
    ${COMMON_INCLUDES}
    ${PLATFORM_INCLUDES}
  )
  
  # ---- 2. Set up compiler definitions ----
  target_compile_definitions(${target_name} PRIVATE
    HAVE_OCCT HAVE_TKG2d HAVE_TKG3d HAVE_TKGeomBase HAVE_TKBRep
  )
  
  # ---- 3. Set up linking with proper dependency handling ----
  if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    # For GCC, use linker groups to handle circular dependencies
    target_link_options(${target_name} PRIVATE "-Wl,--no-as-needed" "-Wl,--start-group")
    link_occt_libraries(${target_name})
    target_link_options(${target_name} PRIVATE "-Wl,--end-group")
  else()
    # For other compilers, just link normally
    link_occt_libraries(${target_name})
  endif()
endfunction()

# Windows MSVC options now incorporated into set_include_directories

# Define a unified function to create and configure a nanobind module with OCCT
function(add_nanobind_extension name)
  # Allow multiple source files using ${ARGN}
  nanobind_add_module(${name} STABLE_ABI NB_STATIC ${ARGN})
  
  # Apply precompiled headers
  target_precompile_headers(${name} PRIVATE src/compas.h)
  
  # Configure includes, definitions, and linking in one call
  configure_target_for_occt(${name})
  
  # Ensure dependencies are built first
  add_dependencies(${name} all_deps_ready)
  
  # Install the module to the correct destination
  install(TARGETS ${name} LIBRARY DESTINATION compas_occt)
endfunction()

# =============================================================================
# SECTION 5: DEPENDENCY TARGETS
# =============================================================================

# Create main dependency target
add_custom_target(all_deps_ready)

# Link appropriate dependencies based on what needs to be downloaded
if(EIGEN_DOWNLOAD_NEEDED)
  add_dependencies(all_deps_ready eigen_download)
endif()
if(OCCT_DOWNLOAD_NEEDED)
  add_dependencies(all_deps_ready occt_external)
endif()

# =============================================================================
# SECTION 6: PYTHON MODULE TARGETS
# =============================================================================

add_nanobind_extension(_primitives src/primitives.cpp)
add_nanobind_extension(_curves src/curves.cpp)