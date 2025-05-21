cmake_minimum_required(VERSION 3.15)
project(compas_occt LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(ExternalProject)
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module Development.SABIModule)
find_package(nanobind CONFIG REQUIRED)
find_package(Threads REQUIRED)

# ------------------------------------------------------------------------------
# Eigen (header-only library)
# ------------------------------------------------------------------------------
set(EIGEN_DIR "${CMAKE_CURRENT_SOURCE_DIR}/external/eigen")
file(MAKE_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/external") # Create directories if they don't exist
add_custom_target(eigen_ext) # Create a target for Eigen tracking
set(EIGEN_TARGET eigen_ext)

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

add_custom_target(external_downloads) # Create a target for all external dependencies
add_dependencies(external_downloads eigen_ext)

# ------------------------------------------------------------------------------
# OCCT
# ------------------------------------------------------------------------------
set(CMAKE_DEPS_DIR ${CMAKE_BINARY_DIR}/deps)
set(OCCT_PREFIX ${CMAKE_DEPS_DIR}/occt) # Create needed directories
file(MAKE_DIRECTORY ${CMAKE_DEPS_DIR})
set(OCCT_SRC_DIR ${OCCT_PREFIX}/src/occt)
set(OCCT_BUILD_DIR ${OCCT_PREFIX}/src/occt-build)
set(OCCT_INSTALL_DIR ${OCCT_PREFIX}/install)
set(OCCT_ALREADY_BUILT FALSE CACHE BOOL "Flag to indicate if OCCT has been built")

# Set platform-specific library prefixes and extensions
if(WIN32)
    set(LIB_PREFIX "")
    set(LIB_EXT ".lib")
    set(OCCT_LIB_DIR "${OCCT_BUILD_DIR}/win64/vc14/lib")
    set(OCCT_INCLUDE_DIR "${OCCT_INSTALL_DIR}/inc")
elseif(APPLE)
    set(LIB_PREFIX "lib")
    set(LIB_EXT ".a")
    set(OCCT_LIB_DIR "${OCCT_BUILD_DIR}/mac64/lib")
    set(OCCT_INCLUDE_DIR "${OCCT_INSTALL_DIR}/include/opencascade")
else() # Linux
    set(LIB_PREFIX "lib")
    set(LIB_EXT ".a")
    set(OCCT_LIB_DIR "${OCCT_BUILD_DIR}/lin64/lib")
    set(OCCT_INCLUDE_DIR "${OCCT_INSTALL_DIR}/include/opencascade")
endif()

# Generate the library targets list using OCCT_LIB_DIR already set for each platform
set(OCCT_LIB_TARGETS "")
set(OCCT_MODULES TKBool TKFillet TKOffset TKFeat TKPrim TKBO TKMesh TKHLR TKShHealing TKTopAlgo TKGeomAlgo TKBRep TKGeomBase TKG3d TKG2d TKMath TKernel)
foreach(MODULE ${OCCT_MODULES})
    list(APPEND OCCT_LIB_TARGETS "${OCCT_LIB_DIR}/${LIB_PREFIX}${MODULE}${LIB_EXT}")
endforeach()

# Always create OCCT targets for dependency tracking
add_custom_target(occt_ext)
set(OCCT_TARGET occt_ext)

if(NOT OCCT_ALREADY_BUILT)
    ExternalProject_Add(
        occt_download
        URL https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V7_9_0.zip
        PREFIX ${OCCT_PREFIX}
        SOURCE_DIR ${OCCT_SRC_DIR}
        BINARY_DIR ${OCCT_BUILD_DIR}
        CMAKE_ARGS
            -DCMAKE_INSTALL_PREFIX=${OCCT_INSTALL_DIR}
            -DCMAKE_BUILD_TYPE=Release
            -DBUILD_LIBRARY_TYPE=Static
            -DBUILD_MODULE_Draw=OFF
            -DBUILD_MODULE_ApplicationFramework=OFF
            -DBUILD_MODULE_DataExchange=OFF
            -DBUILD_MODULE_Visualization=OFF
            -DBUILD_SAMPLES_QT=OFF
            -DBUILD_MODULE_Modeling=ON
            -DBUILD_USE_PCH=OFF
        BUILD_COMMAND ${CMAKE_COMMAND} --build . --config Release -j2
        INSTALL_COMMAND ${CMAKE_COMMAND} --install . --config Release --component Development
        LOG_DOWNLOAD ON
        LOG_CONFIGURE ON
        LOG_BUILD ON
        LOG_INSTALL ON
        BUILD_BYPRODUCTS ${OCCT_LIB_TARGETS}
    )
    
    add_dependencies(external_downloads occt_download)
    add_dependencies(occt_ext occt_download)
    set(OCCT_ALREADY_BUILT TRUE CACHE BOOL "Flag to indicate if OCCT has been built" FORCE)
endif()

# ------------------------------------------------------------------------------
# Build nanobind Python modules
# ------------------------------------------------------------------------------

function(add_nanobind_module module_name source_file)
    nanobind_add_module(${module_name} ${source_file})
    target_include_directories(${module_name} SYSTEM PRIVATE ${EIGEN_DIR} ${OCCT_INCLUDE_DIR})
    if(WIN32)
        target_include_directories(${module_name} SYSTEM PRIVATE ${OCCT_SRC_DIR}/inc ${OCCT_BUILD_DIR}/inc)
    endif()
    add_dependencies(${module_name} ${EIGEN_TARGET} ${OCCT_TARGET})
    target_link_libraries(${module_name} PRIVATE ${OCCT_LIB_TARGETS})
    install(TARGETS ${module_name} LIBRARY DESTINATION compas_occt)
endfunction()

add_nanobind_module(_primitives src/primitives.cpp)
add_nanobind_module(_curves src/curves.cpp)