# Setup script for the Switchboard Python module
# Copyright (C) 2023 Zero ASIC

from setuptools import setup, find_packages
try:
    from pybind11.setup_helpers import Pybind11Extension, build_ext
except ImportError:
    from setuptools import Extension as Pybind11Extension
    from setuptools import build_ext

__version__ = "0.0.7"

# the pybind module is built as _switchboard that is imported
# into the module called "switchboard".  this will allow us
# to implement some features in pure Python in the future

ext_modules = [
    Pybind11Extension(
        "_switchboard",
        ["python/switchboard_pybind.cc"],
        include_dirs=['switchboard/cpp']
    ),
]

# note that numpy is required for this module, because it
# provides a convenient way for moving data between C++
# and Python

setup(
    name="switchboard",
    version=__version__,
    author="ZeroASIC",
    url="https://github.com/zeroasiccorp/switchboard",
    ext_modules=ext_modules,
    setup_requires=['pybind11~=2.6.1'],
    install_requires=['numpy'],
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    include_package_data=True,
    python_requires=">=3.7",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'sbtcp=switchboard.sbtcp:main',
            'switchboard=switchboard.switchboard:main'
        ]
    }
)
