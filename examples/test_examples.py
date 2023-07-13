#!/usr/bin/env python3

import pytest
from pathlib import Path

# import "test_cmd" utility function without the "test_" prefix
# this prevents pytest from incorrectly identifying this function
# as a test function to be run directly
from switchboard.test_util import test_cmd as tcmd

THIS_DIR = Path(__file__).resolve().parent


@pytest.mark.parametrize('path,expected,target', [
    ['minimal', 'PASS!', 'verilator'],
    ['minimal', 'PASS!', 'icarus'],
    ['old_ebrick_cpu_verif', 'Hello World!', None],
    ['old_riscv_grid', 'Hello World!', 'hello'],
    ['old_umidriver', ['correct: 2', 'incorrect: 0'], None],
    ['old_umiram', None, 'python'],
    ['old_umiram', 'PASS!', 'cpp'],
    ['umiram', None, 'python'],
    ['umiram', None, 'cpp'],
    ['python', 'PASS!', None],
    ['router', 'PASS!', None],
    ['stream', 'PASS!', None],
    ['tcp', 'PASS!', None],
    ['umi_endpoint', None, None],
    ['umi_fifo', None, None],
    ['umi_fifo_flex', None, None],
    ['umi_splitter', None, None]
])
def test_make(path, expected, target):
    cmd = ['make']

    if target is not None:
        cmd += [target]

    tcmd(cmd, expected, path=THIS_DIR / path)
