"""Build the `energy_cpp` extension module with pybind11.

Build with pip (recommended), from this directory:

    py -m pip install .

or editable (rebuilds on change):

    py -m pip install -e .

Set ENERGY_CPP_NO_OPENMP=1 to build without OpenMP:

    set ENERGY_CPP_NO_OPENMP=1  &&  py -m pip install .

The extension is optional: the Python pipeline imports it lazily through
src/cpp_bridge.py and keeps working when it is absent.
"""
import os
import sys

from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

__version__ = "1.0.0"

compile_args: list[str] = []
link_args: list[str] = []
use_openmp = not os.environ.get("ENERGY_CPP_NO_OPENMP", "") == "1"

if sys.platform == "win32":
    # MSVC (the default pip toolchain on Windows).
    compile_args.append("/O2")
    if use_openmp:
        compile_args.append("/openmp")
else:
    compile_args.append("-O3")
    if use_openmp:
        compile_args.append("-fopenmp")
        link_args.append("-fopenmp")

ext_modules = [
    Pybind11Extension(
        "energy_cpp",
        sources=[
            "src/bindings.cpp",
            "src/pca.cpp",
            "src/kmeans.cpp",
        ],
        include_dirs=["include"],
        cxx_std=17,
        extra_compile_args=compile_args,
        extra_link_args=link_args,
    ),
]

setup(
    name="energy-cpp-engine",
    version=__version__,
    description=(
        "C++ performance engine for PCA (symmetric Jacobi) and K-Means "
        "(Lloyd + K-Means++). Python/scikit-learn remains the scientific "
        "reference; this module is a performance-oriented alternative."
    ),
    long_description=(
        "Optional pybind11 module for the Energy Consumption Pattern "
        "Analysis project. Importable as `energy_cpp`; consumed through "
        "src/cpp_bridge.py. The Python pipeline functions without it."
    ),
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.12",
)
