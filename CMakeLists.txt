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
include(ExternalProject)

# Define paths for external libraries
set(EXTERNAL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external")

# ---------------------- Eigen (header-only library) ----------------------
set(EIGEN_INCLUDE_DIR "${EXTERNAL_DIR}/eigen")
set(EIGEN_DOWNLOAD_NEEDED FALSE)

if(NOT EXISTS "${EIGEN_INCLUDE_DIR}")
  message(STATUS "Eigen headers not found. Will download.")
  set(EIGEN_DOWNLOAD_NEEDED TRUE)
else()
  message(STATUS "Using existing Eigen headers at: ${EIGEN_INCLUDE_DIR}")
endif()

# -------------------- Template static library --------------------------
set(TEMPLATE_LIB_DIR "${EXTERNAL_DIR}/template_cpp_static_library")
# Use binary directory instead of source directory to avoid conflicts
set(TEMPLATE_LIB_BUILD_DIR "${CMAKE_CURRENT_BINARY_DIR}/template_static_lib_build")
set(TEMPLATE_LIB_INCLUDE_DIR "${TEMPLATE_LIB_DIR}/src")
set(TEMPLATE_LIB_LIBRARY "${TEMPLATE_LIB_BUILD_DIR}/libcpp_static_lib.a")
set(TEMPLATE_LIB_DOWNLOAD_NEEDED FALSE)

if(NOT EXISTS "${TEMPLATE_LIB_LIBRARY}")
  message(STATUS "Template static library not found. Will download and build.")
  set(TEMPLATE_LIB_DOWNLOAD_NEEDED TRUE)
else()
  message(STATUS "Using existing template static library at: ${TEMPLATE_LIB_LIBRARY}")
endif()

# Create external downloads target
add_custom_target(external_downloads ALL)

# -------------------- Download and build external dependencies --------------------

# Download Eigen if needed
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

# Don't clean build directory anymore, as we want to reuse if it exists
# Create/download the template static library only if needed
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
    # Create a dummy target to maintain the dependency chain when the library already exists
    add_custom_target(template_cpp_static_library 
        COMMAND ${CMAKE_COMMAND} -E echo "Using existing static library at ${TEMPLATE_LIB_LIBRARY}"
    )
    add_dependencies(external_downloads template_cpp_static_library)
endif()

# Create an imported target for the static library
add_library(cpp_static_lib STATIC IMPORTED GLOBAL)
set_property(TARGET cpp_static_lib PROPERTY IMPORTED_LOCATION "${TEMPLATE_LIB_LIBRARY}")
add_dependencies(cpp_static_lib template_cpp_static_library)

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
  
  # Make sure the module depends on the external library being built
  add_dependencies(${name} template_cpp_static_library)
  
  # Link directly to the static library file (not using an imported target)
  target_link_libraries(${name} PRIVATE "${TEMPLATE_LIB_LIBRARY}")
  
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
