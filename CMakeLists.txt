cmake_minimum_required(VERSION 3.15)
project(compas_occt LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(ExternalProject)
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module OPTIONAL_COMPONENTS Development.SABIModule)
# Set the path to find nanobind's CMake config
list(APPEND CMAKE_PREFIX_PATH "${Python_SITELIB}/nanobind/cmake")
find_package(nanobind CONFIG REQUIRED)
find_package(Threads REQUIRED)

# ------------------------------------------------------------------------------
# Eigen (header-only library)
# ------------------------------------------------------------------------------
set(EIGEN_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external/eigen")
file(MAKE_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/external") # Create directories if they don't exist
add_custom_target(eigen_ext) # This two-target approach solves the issue of first downloading then building our libraries
message(STATUS "---------------------- Eigen: ${EIGEN_DIR}")

if(NOT EXISTS "${EIGEN_DIR}/Eigen")
    ExternalProject_Add(
        eigen_download
        URL https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip
        PREFIX ${CMAKE_BINARY_DIR}/deps/eigen
        SOURCE_DIR ${EIGEN_DIR}
        CONFIGURE_COMMAND ""
        BUILD_COMMAND ""
        INSTALL_COMMAND ""
        TEST_COMMAND ""
    )
    add_dependencies(eigen_ext eigen_download)
endif()

# ------------------------------------------------------------------------------
# OCCT (static libraries)
# ------------------------------------------------------------------------------
set(CMAKE_DEPS_DIR ${CMAKE_BINARY_DIR}/deps)
set(OCCT_PREFIX ${CMAKE_DEPS_DIR}/occt) # Create needed directories
file(MAKE_DIRECTORY ${CMAKE_DEPS_DIR})
set(OCCT_SRC_DIR ${OCCT_PREFIX}/src/occt)
set(OCCT_BUILD_DIR ${OCCT_PREFIX}/src/occt-build)
set(OCCT_INSTALL_DIR ${OCCT_PREFIX}/install) # Use the same custom install path as specified in ExternalProject_Add
set(OCCT_INCLUDE_DIR "${OCCT_INSTALL_DIR}/my_include" CACHE PATH "Path to OCCT headers" FORCE) # Use the same custom include path as specified in ExternalProject_Add
set(OCCT_LIB_DIR "${OCCT_INSTALL_DIR}/my_shared_libs" CACHE PATH "Path to OCCT libraries" FORCE)

message(STATUS "---------------------- OCCT_INCLUDE_DIR: ${OCCT_INCLUDE_DIR}")
message(STATUS "---------------------- OCCT_LIB_DIR: ${OCCT_LIB_DIR}")

# Platform-specific library settings
if(WIN32)
    set(LIB_PREFIX "")
    set(LIB_EXT ".dll")
    set(RPATH_ORIGIN "")  # Windows doesn't use RPATH
elseif(APPLE)
    set(LIB_PREFIX "lib")
    set(LIB_EXT ".dylib")
    set(RPATH_ORIGIN "@loader_path")
else()
    set(LIB_PREFIX "lib")
    set(LIB_EXT ".so")
    set(RPATH_ORIGIN "$ORIGIN")
endif()

# OCCT has many dynamic libraries. Generate the library targets list using OCCT_LIB_DIR.
set(OCCT_LIB_TARGETS "")
# OCCT modules for dynamic linking - core modules needed for functionality
set(OCCT_MODULES 
    # Base modules
    TKernel TKMath 
    # Geometry modules
    TKG2d TKG3d TKGeomBase TKGeomAlgo TKBRep 
    # Topology modules
    TKTopAlgo TKShHealing 
    # Boolean operations
    TKBool TKBO 
    # Modeling modules
    TKFillet TKOffset TKFeat TKPrim TKMesh 
    # STEP modules
    TKCDF TKLCAF TKCAF TKV3d
    TKService 
    TKXSBase TKDE 
    # Data exchange modules
    TKXCAF TKDESTEP
    # Binary and XML persistence
    TKBin TKXml TKStd TKStdL TKBinL TKXmlL
    # Other modules
    TKTObj TKBinTObj TKXmlTObj
)

# # Add modeling libraries
# list(APPEND OCCT_MODULES TKBool TKFillet TKOffset TKFeat TKPrim TKBO)

# # Add mesh and healing libraries (exclude TKXMesh to avoid symbol conflicts)
# list(APPEND OCCT_MODULES TKMesh TKHLR TKShHealing)

# # Add STEP support libraries from DataExchange module
# list(APPEND OCCT_MODULES TKDESTEP TKDE TKXSBase)

# # Add Application Framework and XCAF libraries for STEP support
# list(APPEND OCCT_MODULES TKXCAF TKLCAF TKCAF TKBinXCAF TKBin TKCDF TKXmlXCAF TKXml TKStd)

# # Add remaining libraries (excluding ones with known symbol conflicts)
# list(APPEND OCCT_MODULES TKBinL TKBinTObj TKStdL TKTObj TKXmlL TKXmlTObj TKService)
foreach(MODULE ${OCCT_MODULES})
    list(APPEND OCCT_LIB_TARGETS "${OCCT_LIB_DIR}/${LIB_PREFIX}${MODULE}${LIB_EXT}")
endforeach()

add_custom_target(occt_ext) # This two-target approach solves the issue of first downloading then building our libraries

if(NOT EXISTS "${OCCT_INSTALL_DIR}/my_include" OR NOT EXISTS "${OCCT_INSTALL_DIR}/my_shared_libs")
    ExternalProject_Add(
        occt_download
        URL https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V7_9_0.zip
        SOURCE_DIR ${OCCT_SRC_DIR}
        BINARY_DIR ${OCCT_BUILD_DIR}
        INSTALL_DIR ${OCCT_INSTALL_DIR}
        CMAKE_ARGS
            -DCMAKE_BUILD_TYPE=Release
            -DBUILD_LIBRARY_TYPE=Shared
            -DUSE_FREEIMAGE=OFF
            -DUSE_FFMPEG=OFF
            -DUSE_TBB=OFF
            -DUSE_VTK=OFF
            -DUSE_FREETYPE=OFF
            -DINSTALL_DIR_INCLUDE=my_include
            -DINSTALL_DIR_LIB=my_shared_libs
            -DCMAKE_INSTALL_PREFIX=${OCCT_INSTALL_DIR}
            # Use compatible build settings
            -DCMAKE_C_FLAGS=-fPIC
            -DCMAKE_CXX_FLAGS=-fPIC
            -DBUILD_MODULE_Draw=OFF
            -DBUILD_MODULE_ApplicationFramework=ON
            -DBUILD_MODULE_DataExchange=ON
            -DBUILD_MODULE_Visualization=OFF
            # Ensure RTTI is enabled for OCCT build
            -DCMAKE_CXX_FLAGS="-frtti"
            -DBUILD_USE_PCH=ON
            # Remove 3rd parties
            -DUSE_XLIB=OFF
            -DUSE_TK=OFF
            -DUSE_OPENGL=OFF
            -DUSE_GLES2=OFF
            -DUSE_EIGEN=OFF
            -DUSE_OPENVR=OFF
            -DUSE_DRACO=OFF
            -DUSE_RAPIDJSON=OFF
            -DUSE_QT=OFF
        # Must build AND install the libraries to the custom location
        BUILD_COMMAND ${CMAKE_COMMAND} --build . --config Release # -j4
        INSTALL_COMMAND ${CMAKE_COMMAND} --install . --config Release
        BUILD_BYPRODUCTS ${OCCT_LIB_TARGETS}
    )
    
    add_dependencies(occt_ext occt_download)
endif()

# Ensure RTTI is enabled for our build as well
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -frtti")

# ------------------------------------------------------------------------------
# RPATH configuration to ensure OCCT libraries can be found at runtime
# ------------------------------------------------------------------------------
# Set RPATH for all targets
set(CMAKE_INSTALL_RPATH "${OCCT_LIB_DIR}")
set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)

# Use the RPATH for installed binaries/libraries
if(NOT APPLE)
    set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
    set(CMAKE_SKIP_BUILD_RPATH FALSE)
else()
    # macOS-specific RPATH settings
    set(CMAKE_MACOSX_RPATH ON)
endif()

# ------------------------------------------------------------------------------
# Build nanobind Python modules
# ------------------------------------------------------------------------------

function(add_nanobind_module module_name source_file)
    nanobind_add_module(${module_name} STABLE_ABI NB_STATIC ${source_file})                               # Creates the Python extension module with nanobind using stable ABI
    target_include_directories(${module_name} SYSTEM PRIVATE ${EIGEN_DIR} ${OCCT_INCLUDE_DIR})  # Add include paths for headers (SYSTEM suppresses warnings)
    add_dependencies(${module_name} eigen_ext occt_ext)                                         # Ensures Eigen and OCCT are built before this module
    
    # Set visibility flags for RTTI symbols and improve linkage
    target_compile_options(${module_name} PRIVATE -frtti -fvisibility=default)
    set_target_properties(${module_name} PROPERTIES ENABLE_EXPORTS ON)
    
    # Configure RPATH for dynamic libraries (Unix-like systems only)
    if(NOT WIN32)
        set_target_properties(${module_name} PROPERTIES
            BUILD_RPATH "${OCCT_LIB_DIR}"
            INSTALL_RPATH "${RPATH_ORIGIN}/lib"  # Platform-specific relative path
            BUILD_RPATH_USE_ORIGIN TRUE
            INSTALL_RPATH_USE_LINK_PATH FALSE
        )
    endif()
    
    # Standard linking for dynamic libraries
    target_link_libraries(${module_name} PRIVATE ${OCCT_LIB_TARGETS})
    
    # Optional: Add linker flags for better symbol resolution
    if(UNIX AND NOT APPLE)
        target_link_options(${module_name} PRIVATE -Wl,--no-as-needed)
    endif()
    
    install(TARGETS ${module_name} LIBRARY DESTINATION compas_occt)                             # Installs the compiled module to the compas_occt package
endfunction()

add_nanobind_module(_primitives src/primitives.cpp)
add_nanobind_module(_curves src/curves.cpp)
add_nanobind_module(_nurbssurface src/nurbssurface.cpp)
add_nanobind_module(_step src/step.cpp)

# Install OCCT shared libraries with the Python package for wheel distribution
# This replaces the need for repair tools (auditwheel/delocate/delvewheel)
if(WIN32)
    # On Windows, install DLLs in the same directory as Python modules
    install(DIRECTORY ${OCCT_LIB_DIR}/
        DESTINATION compas_occt
        FILES_MATCHING PATTERN "*.dll"
        PATTERN "*.lib" EXCLUDE
        PATTERN "*.pdb" EXCLUDE
    )
else()
    # On Unix-like systems, install in lib/ subdirectory
    install(DIRECTORY ${OCCT_LIB_DIR}/
        DESTINATION compas_occt/lib
        FILES_MATCHING 
            PATTERN "*.so*"    # Linux shared libraries
            PATTERN "*.dylib*" # macOS dynamic libraries
        PATTERN "*.a" EXCLUDE   # Exclude static libraries
        PATTERN "*.la" EXCLUDE  # Exclude libtool archives
    )
    
    # Also install any symlinks (important for versioned libraries)
    # Note: CMake will automatically follow symlinks when copying files
    install(DIRECTORY ${OCCT_LIB_DIR}/
        DESTINATION compas_occt/lib
        FILES_MATCHING PATTERN "*.so"
    )
endif()