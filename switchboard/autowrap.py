# Tool for automatically wrapping a DUT with switchboard interfaces

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from pathlib import Path
from copy import deepcopy

from .umi import UmiTxRx
from .axi import AxiTxRx
from .axil import AxiLiteTxRx

from _switchboard import PySbTx, PySbRx


def normalize_interface(name, value):
    # copy before modifying
    value = deepcopy(value)

    assert isinstance(value, dict)

    if 'type' not in value:
        value['type'] = 'sb'

    assert 'type' in value
    value['type'] = normalize_intf_type(value['type'])
    type = value['type']

    assert 'direction' in value
    value['direction'] = normalize_direction(type=type, direction=value['direction'])

    if type == 'sb':
        if 'dw' not in value:
            value['dw'] = 256
        if 'uri' not in value:
            value['uri'] = f'{name}.q'
    elif type == 'umi':
        if 'dw' not in value:
            value['dw'] = 256
        if 'aw' not in value:
            value['aw'] = 64
        if 'cw' not in value:
            value['cw'] = 32
        if 'txrx' not in value:
            value['txrx'] = None
        if 'uri' not in value:
            value['uri'] = f'{name}.q'
    elif type in ['axi', 'axil']:
        if 'dw' not in value:
            value['dw'] = 32
        if 'aw' not in value:
            value['aw'] = 16
        if 'uri' not in value:
            value['uri'] = name

        if type == 'axi':
            # settings that only apply to AXI, not AXI-Lite

            if 'idw' not in value:
                value['idw'] = 8
    else:
        raise ValueError(f'Unsupported interface type: "{type}"')

    return name, value


def normalize_interfaces(interfaces):
    if interfaces is None:
        interfaces = {}

    retval = {}

    for name, value in interfaces.items():
        name, value = normalize_interface(name, value)
        retval[name] = value

    return retval


def normalize_clock(clock):
    # copy before modifying
    clock = deepcopy(clock)

    if isinstance(clock, str):
        clock = dict(name=clock)

    assert isinstance(clock, dict)

    return clock


def normalize_clocks(clocks):
    if clocks is None:
        clocks = ['clk']

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
        resets = []

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
        tieoffs = {}

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
        parameters = {}

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

    for name, value in interfaces.items():
        type = value['type']
        direction = value['direction']

        if type == 'sb':
            dw = value['dw']

            lines += [tab + f'`SB_WIRES({name}, {dw});']

            if direction_is_input(direction):
                lines += [tab + f'`QUEUE_TO_SB_SIM({name}, {dw}, "");']
            elif direction_is_output(direction):
                lines += [tab + f'`SB_TO_QUEUE_SIM({name}, {dw}, "");']
            else:
                raise Exception(f'Unsupported SB direction: {direction}')
        elif type == 'umi':
            dw = value['dw']
            cw = value['cw']
            aw = value['aw']

            lines += [tab + f'`SB_UMI_WIRES({name}, {dw}, {cw}, {aw});']

            if direction_is_input(direction):
                lines += [tab + f'`QUEUE_TO_UMI_SIM({name}, {dw}, {cw}, {aw}, "");']
            elif direction_is_output(direction):
                lines += [tab + f'`UMI_TO_QUEUE_SIM({name}, {dw}, {cw}, {aw}, "");']
            else:
                raise Exception(f'Unsupported UMI direction: {direction}')
        elif type == 'axi':
            dw = value['dw']
            aw = value['aw']
            idw = value['idw']

            lines += [tab + f'`SB_AXI_WIRES({name}, {dw}, {aw}, {idw});']

            if direction_is_subordinate(direction):
                lines += [tab + f'`SB_AXI_M({name}, {dw}, {aw}, {idw}, "");']
            elif direction_is_manager(direction):
                lines += [tab + f'`SB_AXI_S({name}, {dw}, {aw}, "");']
            else:
                raise Exception(f'Unsupported AXI direction: {direction}')
        elif type == 'axil':
            dw = value['dw']
            aw = value['aw']

            lines += [tab + f'`SB_AXIL_WIRES({name}, {dw}, {aw});']

            if direction_is_subordinate(direction):
                lines += [tab + f'`SB_AXIL_M({name}, {dw}, {aw}, "");']
            elif direction_is_manager(direction):
                lines += [tab + f'`SB_AXIL_S({name}, {dw}, {aw}, "");']
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

    for name, value in interfaces.items():
        type = value['type']

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
    lines += ['']

    # initialize queue connections

    lines += [
        tab + 'string uri_sb_value;',
        '',
        tab + 'initial begin',
        (2 * tab) + '/* verilator lint_off IGNOREDRETURN */'
    ]

    for name, value in interfaces.items():
        lines += [
            (2 * tab) + f'if($value$plusargs("{name}=%s", uri_sb_value)) begin',
            (3 * tab) + f'{name}_sb_inst.init(uri_sb_value);',
            (2 * tab) + 'end'
        ]

    lines += [
        (2 * tab) + '/* verilator lint_on IGNOREDRETURN */',
        tab + 'end'
    ]

    lines += ['']

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
    return direction.lower() in ['m', 'manager', 'master', 'indicator']


def direction_is_subordinate(direction):
    return direction.lower() in ['s', 'subordinate', 'slave', 'target']


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


def directions_are_compatible(type, a, b):
    a = normalize_direction(type, a)
    b = normalize_direction(type, b)

    if type_is_sb(type) or type_is_umi(type):
        return (((a == 'input') and (b == 'output'))
            or ((a == 'output') and (b == 'input')))
    elif type_is_axi(type) or type_is_axil(type):
        return (((a == 'manager') and (b == 'subordinate'))
            or ((a == 'subordinate') and (b == 'manager')))
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


def create_intf_objs(intf_defs, fresh=True, max_rate=-1):
    intf_objs = {}

    umi_txrx = {}

    for name, value in intf_defs.items():
        type = value['type']

        if type.lower() in ['umi']:
            txrx = value['txrx']

            if txrx is not None:
                if txrx not in umi_txrx:
                    umi_txrx[txrx] = dict(tx_uri=None, rx_uri=None)

                if 'srcaddr' in value:
                    umi_txrx[txrx]['srcaddr'] = value['srcaddr']

                if 'posted' in value:
                    umi_txrx[txrx]['posted'] = value['posted']

                if 'max_bytes' in value:
                    umi_txrx[txrx]['max_bytes'] = value['max_bytes']

                if 'max_rate' in value:
                    umi_txrx[txrx]['max_rate'] = value['max_rate']
                else:
                    # use default if not set for this particular interface
                    umi_txrx[txrx]['max_rate'] = max_rate

                direction = value['direction']

                if direction.lower() in ['i', 'in', 'input']:
                    umi_txrx[txrx]['tx_uri'] = value['uri']
                elif direction.lower() in ['o', 'out', 'output']:
                    umi_txrx[txrx]['rx_uri'] = value['uri']
                else:
                    raise Exception(f'Unsupported UMI direction: {direction}')
            else:
                intf_objs[name] = create_intf_obj(value, fresh=fresh, max_rate=max_rate)
        else:
            intf_objs[name] = create_intf_obj(value, fresh=fresh, max_rate=max_rate)

    for key, value in umi_txrx.items():
        intf_objs[key] = UmiTxRx(**value, fresh=fresh)

    return intf_objs


def create_intf_obj(value, fresh=True, max_rate=-1):
    type = value['type']
    direction = value['direction']

    if type_is_sb(type):
        kwargs = {}

        if 'max_rate' in value:
            kwargs['max_rate'] = value['max_rate']
        else:
            # use default if not set for this particular interface
            kwargs['max_rate'] = max_rate

        if direction_is_input(direction):
            obj = PySbTx(value['uri'], fresh=fresh, **kwargs)
        elif direction_is_output(direction):
            obj = PySbRx(value['uri'], fresh=fresh, **kwargs)
        else:
            raise Exception(f'Unsupported SB direction: "{direction}"')
    elif type_is_umi(type):
        kwargs = {}

        if 'max_rate' in value:
            kwargs['max_rate'] = value['max_rate']
        else:
            # use default if not set for this particular interface
            kwargs['max_rate'] = max_rate

        if direction_is_input(direction):
            obj = UmiTxRx(tx_uri=value['uri'], fresh=fresh, **kwargs)
        elif direction_is_output(direction):
            obj = UmiTxRx(rx_uri=value['uri'], fresh=fresh, **kwargs)
        else:
            raise Exception(f'Unsupported UMI direction: "{direction}"')
    elif type_is_axi(type):
        kwargs = {}

        if 'prot' in value:
            kwargs['prot'] = value['prot']

        if 'id' in value:
            kwargs['id'] = value['id']

        if 'size' in value:
            kwargs['size'] = value['size']

        if 'max_beats' in value:
            kwargs['max_beats'] = value['max_beats']

        if 'max_rate' in value:
            kwargs['max_rate'] = value['max_rate']
        else:
            # use default if not set for this particular interface
            kwargs['max_rate'] = max_rate

        if direction_is_subordinate(direction):
            obj = AxiTxRx(uri=value['uri'], data_width=value['dw'],
                addr_width=value['aw'], id_width=value['idw'], **kwargs)
        else:
            raise Exception(f'Unsupported AXI direction: "{direction}"')
    elif type_is_axil(type):
        kwargs = {}

        if 'prot' in value:
            kwargs['prot'] = value['prot']

        if 'max_rate' in value:
            kwargs['max_rate'] = value['max_rate']
        else:
            # use default if not set for this particular interface
            kwargs['max_rate'] = max_rate

        if direction_is_subordinate(direction):
            obj = AxiLiteTxRx(uri=value['uri'], data_width=value['dw'],
                addr_width=value['aw'], **kwargs)
        else:
            raise Exception(f'Unsupported AXI-Lite direction: "{direction}"')
    else:
        raise Exception(f'Unsupported interface type: "{type}"')

    return obj
