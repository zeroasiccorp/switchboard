#!/usr/bin/env python

# Copyright (c) 2026 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import pytest

from switchboard.autowrap import autowrap


def wrap(tmp_path, interfaces, resets):
    filename = autowrap(
        instances={'dut': 'dut'},
        parameters={'dut': {}},
        interfaces={'dut': interfaces},
        clocks={'dut': ['clk']},
        resets={'dut': resets},
        tieoffs={'dut': {}},
        filename=tmp_path / 'testbench.sv'
    )

    return filename.read_text()


# the transactors have to be held in reset for as long as any part of the design
# is in reset.  otherwise transactions are driven into a DUT that hasn't come out
# of reset yet, which hangs the simulation if the DUT holds its "ready" signals
# high during reset.  see https://github.com/zeroasiccorp/switchboard/issues/275

@pytest.mark.parametrize('name,intf,macro', [
    ('sb_in', dict(type='sb', dw=32, direction='input'), 'QUEUE_TO_SB_SIM'),
    ('sb_out', dict(type='sb', dw=32, direction='output'), 'SB_TO_QUEUE_SIM'),
    ('umi_in', dict(type='umi', dw=32, cw=32, aw=64, direction='input'), 'QUEUE_TO_UMI_SIM'),
    ('umi_out', dict(type='umi', dw=32, cw=32, aw=64, direction='output'), 'UMI_TO_QUEUE_SIM'),
    ('s_axi', dict(type='axi', dw=32, aw=16, idw=8, direction='subordinate'), 'SB_AXI_M'),
    ('s_axil', dict(type='axil', dw=32, aw=16, direction='subordinate'), 'SB_AXIL_M'),
])
def test_transactor_held_in_reset(tmp_path, name, intf, macro):
    text = wrap(tmp_path, {name: intf}, [dict(name='rst', delay=8)])

    line = next(line for line in text.splitlines() if macro in line)

    # the transactor reset is the last bit of the reset vector to be de-asserted,
    # making it the logical OR of every reset driven into the design
    assert line.rstrip().endswith('rstvec[8]);'), line

    # the reset vector has to be declared before the transactors that use it
    assert text.index('rstvec = ') < text.index(macro)


def test_transactor_reset_tied_off_without_resets(tmp_path):
    text = wrap(tmp_path, {'s_axil': dict(type='axil', dw=32, aw=16,
        direction='subordinate')}, [])

    assert 'rstvec' not in text

    line = next(line for line in text.splitlines() if 'SB_AXIL_M' in line)
    assert line.rstrip().endswith("1'b0);"), line
