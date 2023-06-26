#!/usr/bin/env python3

import pytest
from switchboard.test_util import test_cmd as tcmd


@pytest.mark.parametrize('mode', ['verilator', 'icarus'])
def test_minimal(mode):
    tcmd(['make', mode], 'PASS!', path='minimal')


def test_old_riscv_grid():
    tcmd(['make', 'hello'], 'Hello World!', path='old_riscv_grid')


def test_old_umidriver():
    tcmd('make', ['correct: 2', 'incorrect: 0'], path='old_umidriver')
