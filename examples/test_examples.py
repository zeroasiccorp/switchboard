#!/usr/bin/env python3

import pytest

# import "test_cmd" utility function without the "test_" prefix
# this prevents pytest from incorrectly identifying this function
# as a test function to be run directly
from switchboard.test_util import test_cmd as tcmd


@pytest.mark.parametrize('mode', ['verilator', 'icarus'])
def test_minimal(mode):
    tcmd(['make', mode], 'PASS!', path='minimal')


def test_old_ebrick_cpu_verif():
    tcmd('make', 'Hello World!', path='old_ebrick_cpu_verif')


def test_old_riscv_grid():
    tcmd(['make', 'hello'], 'Hello World!', path='old_riscv_grid')


def test_old_umidriver():
    tcmd('make', ['correct: 2', 'incorrect: 0'], path='old_umidriver')


@pytest.mark.parametrize('mode', ['python', 'cpp'])
def test_old_umiram(mode):
    tcmd(['make', mode], 'PASS!', path='old_umiram')


@pytest.mark.parametrize('mode', ['python', 'cpp'])
def test_umiram(mode):
    tcmd(['make', mode], path='umiram')


@pytest.mark.parametrize('path', [
    'python',
    'router',
    'stream',
    'tcp'
])
def test_for_pass(path):
    tcmd('make', ['PASS!'], path=path)


@pytest.mark.parametrize('path', [
    'umi_endpoint',
    'umi_fifo',
    'umi_splitter'
])
def test_basic(path):
    tcmd('make', path=path)
