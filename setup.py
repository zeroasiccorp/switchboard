from glob import glob
from setuptools import setup, find_packages
from pybind11.setup_helpers import Pybind11Extension, build_ext

__version__ = "0.0.1"

ext_modules = [
    Pybind11Extension(
        "_switchboard",
        sorted(glob("python/*.cc")),  # Sort source files for reproducibility
        include_dirs=['cpp']
    ),
]

setup(
    name="switchboard",
    version=__version__,
    author="ZeroASIC",
    url="https://github.com/zeroasiccorp/switchboard",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.7",
    packages=find_packages()
)
