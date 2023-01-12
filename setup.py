# Setup script for the Switchboard Python module
# Copyright (C) 2023 Zero ASIC

from setuptools import setup, find_packages
from pybind11.setup_helpers import Pybind11Extension, build_ext

__version__ = "0.0.1"

# the pybind module is built as _switchboard that is imported
# into the module called "switchboard".  this will allow us
# to implement some features in pure Python in the future

ext_modules = [
    Pybind11Extension(
        "_switchboard",
        ["python/switchboard_pybind.cc"],
        include_dirs=['cpp']
    ),
]

# note that numpy is required for this module, because it
# provides a convenient way for moving data between C++
# and Python

setup (
    name="switchboard",
    version=__version__,
    author="ZeroASIC",
    url="https://github.com/zeroasiccorp/switchboard",
    ext_modules=ext_modules,
    setup_requires=['numpy'],
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.7",
    packages=find_packages()
)
