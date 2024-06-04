#!/usr/bin/env python3

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import pytest
from pathlib import Path

# import "test_cmd" utility function without the "test_" prefix
# this prevents pytest from incorrectly identifying this function
# as a test function to be run directly
from switchboard.test_util import test_cmd as tcmd

THIS_DIR = Path(__file__).resolve().parent


@pytest.mark.parametrize('path,expected,target', [
    # ['axil', 'PASS!', 'icarus'],
    # ['axil', 'PASS!', 'verilator'],
    ['minimal', 'PASS!', 'icarus'],
    ['minimal', 'PASS!', 'verilator'],
    # ['network', None, 'verilator'],
    # ['network', None, 'icarus'],
    # ['network', None, 'verilator-single-netlist'],
    # ['network', None, 'icarus-single-netlist'],
    # ['python', 'PASS!', None],
    # ['router', 'PASS!', None],
    # ['stream', 'PASS!', None],
    # ['tcp', 'PASS!', None],
    # ['umi_endpoint', None, None],
    # ['umi_fifo', None, None],
    # ['umi_fifo_flex', None, None],
    # ['umi_gpio', None, None],
    # ['umi_mem_cpp', None, None],
    # ['umi_splitter', None, None],
    # ['umiparam', None, 'verilator'],
    # ['umiparam', None, 'icarus'],
    # ['umiparam-network', None, 'verilator'],
    # ['umiparam-network', None, 'verilator-single-netlist'],
    # ['umiparam-network', None, 'verilator-supernet'],
    # ['umiparam-network', None, 'icarus'],
    # ['umiram', None, 'cpp'],
    # ['umiram', None, 'verilator'],
    # ['xyce', None, 'icarus'],
    # ['xyce', None, 'verilator']
])
def test_make(path, expected, target):
    cmd = ['make']

    if target is not None:
        cmd += [target]

    tcmd(cmd, expected, path=THIS_DIR / path)
