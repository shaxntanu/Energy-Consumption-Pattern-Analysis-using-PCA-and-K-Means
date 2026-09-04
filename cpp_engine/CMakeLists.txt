cmake_minimum_required(VERSION 3.16)
project(energy_cpp_engine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(ENERGY_CPP_OPENMP "Enable OpenMP in the K-Means assignment step" ON)
option(ENERGY_CPP_BUILD_MODULE "Build the pybind11 module (needs pybind11)" OFF)
option(ENERGY_CPP_BUILD_BENCH "Build the standalone benchmark binary" ON)

# Core static library, shared by every target. All algorithm code lives here;
# targets only add the bindings or the benchmark main.
add_library(energy_engine STATIC
  src/pca.cpp
  src/kmeans.cpp
)
target_include_directories(energy_engine PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

if(ENERGY_CPP_OPENMP)
  find_package(OpenMP COMPONENTS CXX QUIET)
  if(OpenMP_CXX_FOUND)
    target_link_libraries(energy_engine PUBLIC OpenMP::OpenMP_CXX)
    message(STATUS "energy_cpp_engine: OpenMP enabled")
  else()
    message(WARNING "energy_cpp_engine: OpenMP requested but not found; building single-threaded")
  endif()
endif()

if(ENERGY_CPP_BUILD_BENCH)
  add_executable(energy_bench benchmarks/bench_main.cpp)
  target_link_libraries(energy_bench PRIVATE energy_engine)
endif()

if(ENERGY_CPP_BUILD_MODULE)
  find_package(pybind11 CONFIG QUIET)
  if(NOT pybind11_FOUND)
    find_package(Python COMPONENTS Interpreter Development.Module QUIET)
    if(Python_FOUND)
      execute_process(
        COMMAND ${Python_EXECUTABLE} -m pybind11 --cmakedir
        OUTPUT_VARIABLE _pybind11_cmakedir OUTPUT_STRIP_TRAILING_WHITESPACE)
      list(APPEND CMAKE_PREFIX_PATH "${_pybind11_cmakedir}")
      find_package(pybind11 CONFIG REQUIRED)
    endif()
  endif()
  pybind11_add_module(energy_cpp src/bindings.cpp)
  target_link_libraries(energy_cpp PRIVATE energy_engine)
endif()
