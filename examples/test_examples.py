#!/usr/bin/env python3

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import pytest
from pathlib import Path

# import "test_cmd" utility function without the "test_" prefix
# this prevents pytest from incorrectly identifying this function
# as a test function to be run directly
from switchboard.test_util import test_cmd as tcmd

THIS_DIR = Path(__file__).resolve().parent


@pytest.mark.parametrize('path,expected,target', [
    ['axil', 'PASS!', 'verilator'],
    ['axil', 'PASS!', 'icarus'],
    ['minimal', 'PASS!', 'verilator'],
    ['minimal', 'PASS!', 'icarus'],
    ['umi_mem_cpp', None, None],
    ['umiram', None, 'verilator'],
    ['umiram', None, 'cpp'],
    ['python', 'PASS!', None],
    ['router', 'PASS!', None],
    ['stream', 'PASS!', None],
    ['tcp', 'PASS!', None],
    ['umi_endpoint', None, None],
    ['umi_gpio', None, None],
    ['umi_fifo', None, None],
    ['umi_fifo_flex', None, None],
    ['umi_splitter', None, None],
    ['xyce', None, 'verilator'],
    ['xyce', None, 'icarus']
])
def test_make(path, expected, target):
    cmd = ['make']

    if target is not None:
        cmd += [target]

    tcmd(cmd, expected, path=THIS_DIR / path)
