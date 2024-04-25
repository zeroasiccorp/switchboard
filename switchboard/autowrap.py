# Tool for automatically wrapping a DUT with switchboard interfaces

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from pathlib import Path
from copy import deepcopy


def normalize_interface(interface):
    # copy before modifying
    interface = deepcopy(interface)

    assert 'name' in interface

    if 'type' not in interface:
        interface['type'] = 'sb'

    assert 'type' in interface
    interface['type'] = normalize_intf_type(interface['type'])
    type = interface['type']

    assert 'direction' in interface
    interface['direction'] = normalize_direction(type=type, direction=interface['direction'])

    if type == 'sb':
        if 'dw' not in interface:
            interface['dw'] = 256
    elif type == 'umi':
        if 'dw' not in interface:
            interface['dw'] = 256
        if 'aw' not in interface:
            interface['aw'] = 64
        if 'cw' not in interface:
            interface['cw'] = 32
        if 'txrx' not in interface:
            interface['txrx'] = None
    elif type in ['axi', 'axil']:
        if 'dw' not in interface:
            interface['dw'] = 32
        if 'aw' not in interface:
            interface['aw'] = 16

        if type == 'axi':
            # settings that only apply to AXI, not AXI-Lite

            if 'idw' not in interface:
                interface['idw'] = 8
    else:
        raise ValueError(f'Unsupported interface type: "{type}"')

    return interface


def normalize_interfaces(interfaces):
    if interfaces is None:
        return []

    retval = []

    for interface in interfaces:
        interface = normalize_interface(interface)
        retval.append(interface)

    return retval


def normalize_clock(clock):
    # copy before modifying
    clock = deepcopy(clock)

    if isinstance(clock, str):
        clock = dict(name=clock)

    return clock


def normalize_clocks(clocks):
    if clocks is None:
        return []

    if isinstance(clocks, str):
        clocks = [clocks]

    retval = []

    for clock in clocks:
        clock = normalize_clock(clock)
        retval.append(clock)

    return retval


def normalize_reset(reset):
    # copy before modifying
    reset = deepcopy(reset)

    if isinstance(reset, str):
        reset = {'name': reset}

    assert 'name' in reset

    name = reset['name']

    if 'polarity' not in reset:
        if (('nreset' in name) or ('resetn' in name)
            or ('nrst' in name) or ('rstn' in name)):
            reset['polarity'] = 'negative'
        else:
            reset['polarity'] = 'positive'
    else:
        reset['polarity'] = normalize_polarity(reset['polarity'])

    if 'delay' not in reset:
        reset['delay'] = 0

    return reset


def normalize_resets(resets):
    if resets is None:
        return []

    if isinstance(resets, str):
        resets = [resets]

    retval = []

    for reset in resets:
        reset = normalize_reset(reset)
        retval.append(reset)

    return retval


def normalize_tieoff(key, value):
    # placeholder for doing more interesting things in the future
    return key, value


def normalize_tieoffs(tieoffs):
    if tieoffs is None:
        return {}

    retval = {}

    for key, value in tieoffs.items():
        key, value = normalize_tieoff(key, value)
        retval[key] = value

    return retval


def normalize_parameter(key, value):
    # placeholder for doing more interesting things in the future
    return key, value


def normalize_parameters(parameters):
    if parameters is None:
        return {}

    retval = {}

    for key, value in parameters.items():
        key, value = normalize_parameter(key, value)
        retval[key] = value

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

    parameters = normalize_parameters(parameters)
    interfaces = normalize_interfaces(interfaces)
    clocks = normalize_clocks(clocks)
    resets = normalize_resets(resets)
    tieoffs = normalize_tieoffs(tieoffs)

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

    lines += ['']

    for interface in interfaces:
        name = interface['name']
        type = interface['type']
        direction = interface['direction']

        if type == 'sb':
            dw = interface['dw']

            lines += [tab + f'`SB_WIRES({name}, {dw});']

            if direction_is_input(direction):
                lines += [tab + f'`QUEUE_TO_SB_SIM({name}, {dw}, "{name}.q");']
            elif direction_is_output(direction):
                lines += [tab + f'`SB_TO_QUEUE_SIM({name}, {dw}, "{name}.q");']
            else:
                raise Exception(f'Unsupported SB direction: {direction}')
        elif type == 'umi':
            dw = interface['dw']
            cw = interface['cw']
            aw = interface['aw']

            lines += [tab + f'`SB_UMI_WIRES({name}, {dw}, {cw}, {aw});']

            if direction_is_input(direction):
                lines += [tab + f'`QUEUE_TO_UMI_SIM({name}, {dw}, {cw}, {aw}, "{name}.q");']
            elif direction_is_output(direction):
                lines += [tab + f'`UMI_TO_QUEUE_SIM({name}, {dw}, {cw}, {aw}, "{name}.q");']
            else:
                raise Exception(f'Unsupported UMI direction: {direction}')
        elif type == 'axi':
            dw = interface['dw']
            aw = interface['aw']
            idw = interface['idw']

            lines += [tab + f'`SB_AXI_WIRES({name}, {dw}, {aw}, {idw});']

            if direction_is_subordinate(direction):
                lines += [tab + f'`SB_AXI_M({name}, {dw}, {aw}, {idw}, "{name}");']
            else:
                raise Exception(f'Unsupported AXI direction: {direction}')
        elif type == 'axil':
            dw = interface['dw']
            aw = interface['aw']

            lines += [tab + f'`SB_AXIL_WIRES({name}, {dw}, {aw});']

            if direction_is_subordinate(direction):
                lines += [tab + f'`SB_AXIL_M({name}, {dw}, {aw}, "{name}");']
            else:
                raise Exception(f'Unsupported AXI-Lite direction: {direction}')
        else:
            raise Exception(f'Unsupported interface type: "{type}"')

        lines += ['']

    if len(resets) > 0:
        max_rst_dly = max(reset['delay'] for reset in resets)

        lines += [
            tab + f"reg [{max_rst_dly}:0] rstvec = '1;"
            '',
            tab + 'always @(posedge clk) begin'
        ]

        if max_rst_dly > 0:
            lines += [(2 * tab) + f"rstvec <= {{rstvec[{max_rst_dly - 1}:0], 1'b0}};"]
        else:
            lines += [(2 * tab) + "rstvec <= 1'b0;"]

        lines += [
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

        if type_is_sb(type):
            connections += [f'`SB_CONNECT({name}, {name})']
        elif type_is_umi(type):
            connections += [f'`SB_UMI_CONNECT({name}, {name})']
        elif type_is_axi(type):
            connections += [f'`SB_AXI_CONNECT({name}, {name})']
        elif type_is_axil(type):
            connections += [f'`SB_AXIL_CONNECT({name}, {name})']

    # clocks

    for clock in clocks:
        connections += [f'.{clock["name"]}(clk)']

    # resets

    for reset in resets:
        name = reset['name']
        polarity = reset['polarity']
        delay = reset['delay']

        if polarity_is_positive(polarity):
            value = f'rstvec[{delay}]'
        elif polarity_is_negative(polarity):
            value = f'~rstvec[{delay}]'
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


def direction_is_input(direction):
    return direction.lower() in ['i', 'in', 'input']


def direction_is_output(direction):
    return direction.lower() in ['o', 'out', 'output']


def direction_is_manager(direction):
    return direction.lower() in ['m', 'manager', 'master']


def direction_is_subordinate(direction):
    return direction.lower() in ['s', 'subordinate', 'slave']


def normalize_direction(type, direction):
    if type_is_sb(type) or type_is_umi(type):
        if direction_is_input(direction):
            return 'input'
        elif direction_is_output(direction):
            return 'output'
        else:
            raise Exception(f'Unsupported direction for interface type "{type}": "{direction}"')
    elif type_is_axi(type) or type_is_axil(type):
        if direction_is_manager(direction):
            return 'manager'
        elif direction_is_subordinate(direction):
            return 'subordinate'
        else:
            raise Exception(f'Unsupported direction for interface type "{type}": "{direction}"')
    else:
        raise Exception(f'Unsupported interface type: "{type}"')


def polarity_is_positive(polarity):
    return polarity.lower() in ['+', 'p', 'plus', 'positive']


def polarity_is_negative(polarity):
    return polarity.lower() in ['-', 'n', 'minus', 'negative']


def normalize_polarity(polarity):
    if polarity_is_positive(polarity):
        return 'positive'
    elif polarity_is_negative(polarity):
        return 'negative'
    else:
        raise ValueError(f'Unsupported reset polarity: "{polarity}"')


def type_is_sb(type):
    return type.lower() in ['sb', 'switchboard']


def type_is_umi(type):
    return type.lower() in ['umi']


def type_is_axi(type):
    return type.lower() in ['axi']


def type_is_axil(type):
    return type.lower() in ['axil']


def normalize_intf_type(type):
    if type_is_sb(type):
        return 'sb'
    elif type_is_umi(type):
        return 'umi'
    elif type_is_axi(type):
        return 'axi'
    elif type_is_axil(type):
        return 'axil'
    else:
        raise ValueError(f'Unsupported interface type: "{type}"')
