cmake_minimum_required(VERSION 3.15...3.30)

project(${SKBUILD_PROJECT_NAME} LANGUAGES CXX)

# Find Python
find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)

# Find pybind11
find_package(pybind11 CONFIG REQUIRED)

# Build the extension module
pybind11_add_module(_switchboard MODULE python/switchboard_pybind.cc)

# Include directories
target_include_directories(_switchboard PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/switchboard/cpp)

# Install the extension module into the switchboard package
install(TARGETS _switchboard LIBRARY DESTINATION switchboard)
