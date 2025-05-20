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

# Platform-specific configurations - simplified since cibuildwheels handles architectures separately
if(APPLE)
  # Set minimum macOS version - architecture is now determined by the build environment
  set(CMAKE_OSX_DEPLOYMENT_TARGET "11.00" CACHE STRING "Minimum macOS deployment version" FORCE)
  message(STATUS "Building for macOS")
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
  # Configure OCCT build with minimal required components
  set(OCCT_CMAKE_ARGS
    # Basic build settings
    -DCMAKE_INSTALL_PREFIX=${OCCT_INSTALL_DIR}
    -DCMAKE_BUILD_TYPE=Release
    -DBUILD_LIBRARY_TYPE=Static
    -DBUILD_USE_PCH=OFF
    -DBUILD_OPT_PROFILE=Production
    
    # Disable all optional dependencies
    -DUSE_TK=OFF -DUSE_VTK=OFF -DUSE_FREETYPE=OFF -DUSE_OPENGL=OFF
    
    # Disable samples and tools
    -DBUILD_SAMPLES_MFC=OFF -DBUILD_SAMPLES_QT=OFF -DBUILD_Inspector=OFF -DINSTALL_SAMPLES=OFF
    
    # Disable unneeded modules
    -DBUILD_MODULE_ApplicationFramework=OFF -DBUILD_MODULE_DataExchange=OFF
    -DBUILD_MODULE_Draw=OFF -DBUILD_MODULE_VisualizationTest=OFF -DBUILD_MODULE_Visualization=OFF
  )
  
  # Add platform-specific settings
  if(APPLE)
    # RPATH settings for better library resolution on macOS
    list(APPEND OCCT_CMAKE_ARGS
      "-DCMAKE_OSX_DEPLOYMENT_TARGET=${CMAKE_OSX_DEPLOYMENT_TARGET}"
      "-DCMAKE_MACOSX_RPATH=ON"
      "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON"
      "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=ON"
      "-DBUILD_DOC_Overview=OFF"
    )
  elseif(WIN32)
    # Windows-specific settings
    list(APPEND OCCT_CMAKE_ARGS
      "-G" "Ninja"
      "-DBUILD_MODULE_MODELING=ON"
      "-DBUILD_MODULE_OCAF=OFF"
      "-DINSTALL_FREETYPE=OFF"
    )
  endif()
  
  message(STATUS "Configuring OCCT with platform-specific settings")
  
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

# Helper function to link OCCT libraries in the correct order
function(link_occt_libraries target_name)
  # Group OCCT libraries by functionality for better organization and dependency management
  set(OCCT_BOOL_LIBS
    "${OCCT_LIBRARY_TKBool}"
    "${OCCT_LIBRARY_TKFillet}"
    "${OCCT_LIBRARY_TKOffset}"
    "${OCCT_LIBRARY_TKFeat}"
    "${OCCT_LIBRARY_TKPrim}"
    "${OCCT_LIBRARY_TKBO}"
    "${OCCT_LIBRARY_TKMesh}"
    "${OCCT_LIBRARY_TKHLR}"
    "${OCCT_LIBRARY_TKShHealing}"
  )
  
  set(OCCT_ALGO_LIBS
    "${OCCT_LIBRARY_TKTopAlgo}"
    "${OCCT_LIBRARY_TKGeomAlgo}"
  )
  
  set(OCCT_GEOM_LIBS
    "${OCCT_LIBRARY_TKBRep}"
    "${OCCT_LIBRARY_TKGeomBase}"
    "${OCCT_LIBRARY_TKG3d}"
    "${OCCT_LIBRARY_TKG2d}"
  )
  
  set(OCCT_CORE_LIBS
    "${OCCT_LIBRARY_TKMath}"
    "${OCCT_LIBRARY_TKernel}"
  )
  
  # Link everything in the correct order
  target_link_libraries(${target_name} PRIVATE
    ${OCCT_BOOL_LIBS}
    ${OCCT_ALGO_LIBS}
    ${OCCT_GEOM_LIBS}
    ${OCCT_CORE_LIBS}
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
      # Add OCCT source directories for MSVC
      file(GLOB OCCT_SRC_DIRS LIST_DIRECTORIES true "${OCCT_DIR}/src/*")
      list(APPEND PLATFORM_INCLUDES
        "${OCCT_DIR}/src"
        "${OCCT_DIR}/inc"
        ${OCCT_SRC_DIRS}
      )
      
      # Add include directories as compiler options for better MSVC compatibility
      foreach(DIR "${OCCT_DIR}/inc" "${OCCT_DIR}/src" ${OCCT_SRC_DIRS})
        if(IS_DIRECTORY "${DIR}")
          target_compile_options(${target_name} PRIVATE "/I${DIR}")
        endif()
      endforeach()
    endif()
  else()
    # Unix/Linux/macOS include path is simpler
    set(PLATFORM_INCLUDES
      "${OCCT_INSTALL_DIR}/include/opencascade"
      "${OCCT_DIR}/src"
    )
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

# Define a unified function to create and configure a nanobind module
function(add_nanobind_extension name source)
  # Create the nanobind module with appropriate settings
  nanobind_add_module(${name} STABLE_ABI NB_STATIC ${source})
  
  # Apply precompiled headers for better build times
  target_precompile_headers(${name} PRIVATE src/compas.h)
  
  # Configure includes, definitions, and linking in one call
  configure_target_for_occt(${name})
  
  # Ensure dependencies are built first
  add_dependencies(${name} all_deps_ready)
  
  # Install the module to the correct destination
  install(TARGETS ${name} LIBRARY DESTINATION compas_occt)
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