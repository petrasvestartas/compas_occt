cmake_minimum_required(VERSION 3.15)
project(compas_occt LANGUAGES CXX)

# Build configuration
set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
option(ENABLE_PRECOMPILED_HEADERS "Enable precompiled headers for the build" ON)

# ======================================================================
# External dependencies section
# ======================================================================
include(FetchContent)

# Critical setting: Ensures content is only fetched once and not updated on subsequent builds
# This guarantees your library is built only the first time and reused afterward
set(FETCHCONTENT_UPDATES_DISCONNECTED ON)

# All dependencies will be stored in the build directory
set(DEPS_DIR "${CMAKE_CURRENT_BINARY_DIR}/deps")

# ---------------------- Eigen (header-only library) ----------------------
# FetchContent approach for Eigen
FetchContent_Declare(
  eigen
  URL https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip
  # Remove hash verification since the archive might have changed
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)

if(NOT eigen_POPULATED)
  message(STATUS "Fetching Eigen...")
  FetchContent_Populate(eigen)
endif()

# Add include directory for Eigen
set(EIGEN_INCLUDE_DIR ${eigen_SOURCE_DIR})

# -------------------- Template static library --------------------------
# FetchContent guarantees the library is only built once
# This is much better than ExternalProject_Add for libraries that take a long time to build

FetchContent_Declare(
  template_cpp_static_lib
  GIT_REPOSITORY https://github.com/petrasvestartas/template_cpp_static_library.git
  GIT_TAG main
)

if(NOT template_cpp_static_lib_POPULATED)
  message(STATUS "Fetching and configuring template_cpp_static_library...")
  FetchContent_Populate(template_cpp_static_lib)
  
  # Add the template library as a subdirectory
  # This is the key step - it integrates the library directly into our build
  # ensuring it is only built once
  add_subdirectory(${template_cpp_static_lib_SOURCE_DIR} ${template_cpp_static_lib_BINARY_DIR})
endif()

# Define the paths to use for includes and linking
set(TEMPLATE_LIB_INCLUDE_DIR ${template_cpp_static_lib_SOURCE_DIR}/src)

# The library target is now directly available as a regular CMake target
# We don't need to use separate import targets or fake dependencies
# FetchContent creates proper CMake targets for us

# With FetchContent, we can directly use the target created by the library's CMakeLists.txt
# The target name is defined in the template_cpp_static_library's CMakeLists.txt
# Typically it would be named something like 'cpp_static_lib'

# We're assuming the target is named 'cpp_static_lib' - adjust if needed based on the library's CMake
# If the library doesn't define a target name, you may need to create it yourself

# Find Python and nanobind
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module Development.SABIModule)

find_package(nanobind CONFIG REQUIRED)
find_package(Threads REQUIRED)

# Add include directories
include_directories(
  ${CMAKE_CURRENT_SOURCE_DIR}/src
  ${EIGEN_INCLUDE_DIR}
  ${TEMPLATE_LIB_INCLUDE_DIR}
)

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
    ${nanobind_INCLUDE_DIRS}
  )
  
  # With FetchContent, we can directly link to the library target
  # This ensures proper dependency tracking and avoids hardcoded paths
  target_link_libraries(${name} PRIVATE cpp_static_lib)
  
  # Install the module
  install(TARGETS ${name} LIBRARY DESTINATION compas_occt)
endfunction()

# Create individual extension modules for each C++ file
# Copy this line with new file name and module name
add_nanobind_extension(_primitives src/primitives.cpp)

message(STATUS "============= Build Configuration =============")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Standard: C++${CMAKE_CXX_STANDARD}")
message(STATUS "Eigen Include Dir: ${EIGEN_INCLUDE_DIR}")
message(STATUS "Template Static Library: ${TEMPLATE_LIB_LIBRARY}")
message(STATUS "Template Include Dir: ${TEMPLATE_LIB_INCLUDE_DIR}")
message(STATUS "=======================================")
