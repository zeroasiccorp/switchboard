# Tool for automatically wrapping a DUT with switchboard interfaces

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from pathlib import Path


def normalize_interfaces(interfaces):
    if interfaces is None:
        return []

    retval = []

    for interface in interfaces:
        assert 'name' in interface

        if 'type' not in interface:
            interface['type'] = 'sb'

        assert 'type' in interface
        type = interface['type']

        if type == 'umi':
            if 'dw' not in interface:
                interface['dw'] = 256
            if 'aw' not in interface:
                interface['aw'] = 64
            if 'cw' not in interface:
                interface['cw'] = 32

        retval.append(interface)

    return retval


def normalize_clocks(clocks):
    if clocks is None:
        return []

    if isinstance(clocks, str):
        return [clocks]
    elif isinstance(clocks, (list, set)):
        return clocks
    else:
        raise Exception(f'Unsupported type for "clocks": {type(clocks)}')


def normalize_resets(resets):
    if resets is None:
        return []

    if isinstance(resets, str):
        resets = [resets]

    retval = []

    for value in resets:
        if isinstance(value, str):
            value = {'name': value}

        assert 'name' in value

        name = value['name']

        if 'polarity' not in value:
            if (('nreset' in name) or ('resetn' in name)
                or ('nrst' in name) or ('rstn' in name)):
                value['polarity'] = 'negative'
            else:
                value['polarity'] = 'positive'

        if 'delay' not in value:
            value['delay'] = 0

        retval.append(value)

    return retval


def autowrap(
    design,
    toplevel='testbench',
    parameters=None,
    interfaces=None,
    clocks=None,
    resets=None,
    tieoffs=None,
    filename=None,
    nl='\n',
    tab='    '
):
    # normalize inputs

    interfaces = normalize_interfaces(interfaces)
    clocks = normalize_clocks(clocks)
    resets = normalize_resets(resets)

    # build up output lines

    lines = []

    lines += [
        '`default_nettype none',
        '',
        '`include "switchboard.vh"',
        '',
        f'module {toplevel} (',
        tab + '`ifdef VERILATOR',
        (2 * tab) + 'input clk',
        tab + '`endif',
        ');',
        tab + '`ifndef VERILATOR',
        (2 * tab) + '`SB_CREATE_CLOCK(clk)',
        tab + '`endif',
        ''
    ]

    for key, value in parameters.items():
        lines += [tab + f'parameter {key}={value};']

    lines += ['']

    for interface in interfaces:
        name = interface['name']
        type = interface['type']
        direction = interface['direction']

        if type == 'umi':
            dw = interface['dw']
            cw = interface['cw']
            aw = interface['aw']

            lines += [tab + f'`SB_UMI_WIRES({name}, {dw}, {cw}, {aw});']

            if direction.lower() in ['i', 'in', 'input']:
                lines += [tab + f'`QUEUE_TO_UMI_SIM({name}, {dw}, {cw}, {aw}, "{name}.q");']
            elif direction.lower() in ['o', 'out', 'output']:
                lines += [tab + f'`UMI_TO_QUEUE_SIM({name}, {dw}, {cw}, {aw}, "{name}.q");']
            else:
                raise Exception(f'Unsupported UMI direction: {direction}')

            lines += ['']
        else:
            raise Exception(f'Unsupported interface type: "{type}"')

    lines += [
        tab + "reg reset = 1'b1;"
        '',
        tab + 'always @(posedge clk) begin',
        (2 * tab) + "reset <= 1'b0;",
        tab + 'end',
        ''
    ]

    if len(parameters) > 0:
        lines += [tab + f'{design} #(']
        for n, (key, value) in enumerate(parameters.items()):
            line = (2 * tab) + f'.{key}({value})'

            if n != len(parameters) - 1:
                line += ','

            lines += [line]
        lines += [tab + f') {design}_i (']
    else:
        lines += [tab + f'{design} {design}_i (']

    connections = []

    # interfaces

    for interface in interfaces:
        name = interface['name']
        type = interface['type']

        if type.lower() in ['sb', 'switchboard']:
            connections += [f'`SB_CONNECT({name}, {name})']
        elif type.lower() in ['umi']:
            connections += [f'`SB_UMI_CONNECT({name}, {name})']
        elif type.lower() in ['axi']:
            connections += [f'`SB_AXI_CONNECT({name}, {name})']
        elif type.lower() in ['axi']:
            connections += [f'`SB_AXIL_CONNECT({name}, {name})']

    # clocks

    for clock in clocks:
        connections += [f'.{clock}(clk)']

    # resets

    for reset in resets:
        name = reset['name']
        polarity = reset['polarity']

        if polarity.lower() in ['+', 'p', 'plus', 'positive']:
            value = 'reset'
        elif polarity.lower() in ['-', 'n', 'minus', 'negative']:
            value = '~reset'
        else:
            raise ValueError(f'Unsupported reset polarity: "{polarity}"')

        connections += [f'.{name}({value})']

    # tieoffs

    for key, value in tieoffs.items():
        if value is None:
            value = ''
        else:
            value = str(value)
        connections += [f'.{key}({value})']

    for n, connection in enumerate(connections):
        if n != len(connections) - 1:
            connection += ','
        lines += [(2 * tab) + connection]

    lines += [tab + ');']

    lines += [tab + '`SB_SETUP_PROBES']
    lines += ['']

    lines += ['endmodule']

    lines += ['']

    lines += ['`default_nettype wire']

    if filename is None:
        filename = 'testbench.sv'

    filename = Path(filename).resolve()

    with open(filename, 'w') as f:
        for line in lines:
            f.write(line + nl)

    return filename
