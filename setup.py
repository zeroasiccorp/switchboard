import os
from setuptools import setup, find_packages

name = 'zverif'
version = '0.0.1'

DESCRIPTION = '''\
Tool for verifying chip designs.\
'''

with open('README.md', 'r') as fh:
    LONG_DESCRIPTION = fh.read()

setup(
    name=name,
    version=version,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    keywords = ['verification', 'verilog', 'system-verilog',
                'system verilog', 'verilator', 'spike'],
    packages=find_packages(),
    entry_points = {
        'console_scripts': ['zverif=zverif.zverif:main']
    },
    install_requires=[
        'ubelt',
        'pyyaml'
    ],
    url=f'https://github.com/zeroasiccorp/interposer-verif.git',
    author='Steven Herbst',
    author_email='steven@zeroasic.com',
    python_requires='>=3.7',
    download_url = f'https://github.com/zeroasiccorp/interposer-verif/archive/v{version}.tar.gz',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        f'Programming Language :: Python :: 3.7'
    ],
    include_package_data=True,
    zip_safe=False
)