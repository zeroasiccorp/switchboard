# Setup script for the Switchboard Python module
# Copyright (C) 2023 Zero ASIC

from setuptools import setup, find_packages
from pybind11.setup_helpers import Pybind11Extension, build_ext

__version__ = "0.0.10"

########################################################################
# parse_reqs() from https://github.com/siliconcompiler/siliconcompiler #
########################################################################


def parse_reqs():
    '''Parse out each requirement category from requirements.txt'''
    install_reqs = []
    extras_reqs = {}
    current_section = None  # default to install

    with open('requirements.txt', 'r') as reqs_file:
        for line in reqs_file.readlines():
            line = line.rstrip('\n')
            if line.startswith('#:'):
                # strip off '#:' prefix to read extras name
                current_section = line[2:]
                if current_section not in extras_reqs:
                    extras_reqs[current_section] = []
            elif not line or line.startswith('#'):
                # skip blanks and comments
                continue
            elif current_section is None:
                install_reqs.append(line)
            else:
                extras_reqs[current_section].append(line)

    return install_reqs, extras_reqs

########################################################################
########################################################################


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

# determine installation requirements

install_reqs, extras_req = parse_reqs()

setup(
    name="switchboard",
    version=__version__,
    author="ZeroASIC",
    url="https://github.com/zeroasiccorp/switchboard",
    ext_modules=ext_modules,
    install_requires=install_reqs,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    include_package_data=True,
    python_requires=">=3.7",
    packages=find_packages(),
    extras_require=extras_req,
    entry_points={
        'console_scripts': [
            'sbtcp=switchboard.sbtcp:main',
            'switchboard=switchboard.switchboard:main'
        ]
    }
)
