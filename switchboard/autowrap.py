# Tool for automatically wrapping a DUT with switchboard interfaces

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from pathlib import Path
from copy import deepcopy

from .umi import UmiTxRx
from .axi import AxiTxRx
from .axil import AxiLiteTxRx
from .bitvector import slice_to_msb_lsb

from _switchboard import PySbTx, PySbRx


class WireExpr:
    def __init__(self, width):
        self.width = width
        self.bindings = []

    def bind(self, slice, wire):
        # extract msb, lsb
        msb, lsb = slice_to_msb_lsb(start=slice.start, stop=slice.stop, step=slice.step)

        # make sure that the slice fits in the width
        assert 0 <= lsb <= self.width - 1
        assert 0 <= msb <= self.width - 1

        if len(self.bindings) == 0:
            self.bindings.append(((msb, lsb), wire))
            return

        for idx in range(len(self.bindings) - 1, -1, -1):
            (msb_i, lsb_i), _ = self.bindings[idx]
            if lsb < lsb_i:
                assert msb < lsb_i, \
                    f'bit assignments {msb_i}:{lsb_i} and {msb}:{lsb} overlap'
                self.bindings.insert(idx + 1, ((msb, lsb), wire))
                break
        else:
            (msb_i, lsb_i), _ = self.bindings[0]
            assert lsb > msb_i, \
                f'bit assignments {msb_i}:{lsb_i} and {msb}:{lsb} overlap'
            self.bindings.insert(0, ((msb, lsb), wire))

    def padded(self):
        retval = []

        for idx, ((msb, lsb), wire) in enumerate(self.bindings):
            if idx == 0:
                if msb != self.width - 1:
                    msb_pad = (self.width - 1) - msb
                    retval.append(f"{msb_pad}'b0")

            retval.append(wire)

            if idx < len(self.bindings) - 1:
                lsb_pad = (lsb - 1) - self.bindings[idx + 1][0][0]
            else:
                lsb_pad = lsb

            if lsb_pad > 0:
                retval.append(f"{lsb_pad}'b0")

        return retval

    def __str__(self):
        padded = self.padded()

        if len(padded) == 1:
            return padded[0]
        else:
            return '{' + ', '.join(padded) + '}'


def normalize_interface(name, value):
    # copy before modifying
    value = deepcopy(value)

    assert isinstance(value, dict)

    if 'type' not in value:
        value['type'] = 'sb'

    if 'wire' not in value:
        value['wire'] = name

    assert 'type' in value
    value['type'] = normalize_intf_type(value['type'])
    type = value['type']

    if 'external' not in value:
        if type == 'plusarg':
            value['external'] = False
        else:
            value['external'] = True

    if (type == 'plusarg') and ('direction' not in value):
        value['direction'] = 'input'

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
    elif type == 'gpio':
        if 'width' not in value:
            value['width'] = 1
    elif type == 'plusarg':
        if 'width' not in value:
            value['width'] = 1
        if 'default' not in value:
            value['default'] = 0
        if 'plusarg' not in value:
            value['plusarg'] = name
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
    if isinstance(value, dict):
        value = deepcopy(value)
    else:
        value = {'value': value}

    if 'width' not in value:
        value['width'] = 1

    if 'wire' not in value:
        value['wire'] = None

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
    instances,
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

    parameters = {k: normalize_parameters(v) for k, v in parameters.items()}
    interfaces = {k: normalize_interfaces(v) for k, v in interfaces.items()}
    clocks = {k: normalize_clocks(v) for k, v in clocks.items()}
    resets = {k: normalize_resets(v) for k, v in resets.items()}
    tieoffs = {k: normalize_tieoffs(v) for k, v in tieoffs.items()}

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

    # wire declarations

    wires = {}

    lines += ['']

    # declare all GPIO output wires (makes things easier when an output is
    # sent to multiple places or slices of it are used)

    wires['gpio'] = set()

    for instance in instances:
        for name, value in interfaces[instance].items():
            type = value['type']
            direction = value['direction']

            if not ((type == 'gpio') and (direction == 'output')):
                continue

            wire = value['wire']

            if wire is None:
                # means that the output is unused
                continue

            assert wire not in wires['gpio']

            width = value['width']

            lines += [tab + f'wire [{width-1}:0] {wire};']

            wires['gpio'].add(wire)

    lines += ['']

    for instance in instances:
        # declare wires for tieoffs

        for key, value in tieoffs[instance].items():
            if value['value'] is None:
                continue

            if value['wire'] is None:
                value['wire'] = f'{instance}_tieoff_{key}'

            width = value['width']
            wire = value["wire"]

            lines += [tab + f'wire [{width-1}:0] {wire};']

            lines += [tab + f'assign {wire} = {value["value"]};']

        lines += ['']

        # declare wires for interfaces

        for name, value in interfaces[instance].items():
            type = value['type']

            if type not in wires:
                wires[type] = set()

            wire = value['wire']

            if (type != 'gpio') and (wire not in wires[type]):
                decl_wire = True
                wires[type].add(wire)
            else:
                decl_wire = False

            direction = value['direction']

            external = value['external']

            if type == 'sb':
                dw = value['dw']

                if decl_wire:
                    lines += [tab + f'`SB_WIRES({wire}, {dw});']

                if external:
                    if direction_is_input(direction):
                        lines += [tab + f'`QUEUE_TO_SB_SIM({wire}, {dw}, "");']
                    elif direction_is_output(direction):
                        lines += [tab + f'`SB_TO_QUEUE_SIM({wire}, {dw}, "");']
                    else:
                        raise Exception(f'Unsupported SB direction: {direction}')
            elif type == 'umi':
                dw = value['dw']
                cw = value['cw']
                aw = value['aw']

                if decl_wire and (wire is not None):
                    lines += [tab + f'`SB_UMI_WIRES({wire}, {dw}, {cw}, {aw});']

                if external:
                    if direction_is_input(direction):
                        lines += [tab + f'`QUEUE_TO_UMI_SIM({wire}, {dw}, {cw}, {aw}, "");']
                    elif direction_is_output(direction):
                        lines += [tab + f'`UMI_TO_QUEUE_SIM({wire}, {dw}, {cw}, {aw}, "");']
                    else:
                        raise Exception(f'Unsupported UMI direction: {direction}')
            elif type == 'axi':
                dw = value['dw']
                aw = value['aw']
                idw = value['idw']

                if decl_wire:
                    lines += [tab + f'`SB_AXI_WIRES({wire}, {dw}, {aw}, {idw});']

                if external:
                    if direction_is_subordinate(direction):
                        lines += [tab + f'`SB_AXI_M({wire}, {dw}, {aw}, {idw}, "");']
                    elif direction_is_manager(direction):
                        lines += [tab + f'`SB_AXI_S({wire}, {dw}, {aw}, "");']
                    else:
                        raise Exception(f'Unsupported AXI direction: {direction}')
            elif type == 'axil':
                dw = value['dw']
                aw = value['aw']

                if decl_wire:
                    lines += [tab + f'`SB_AXIL_WIRES({wire}, {dw}, {aw});']

                if external:
                    if direction_is_subordinate(direction):
                        lines += [tab + f'`SB_AXIL_M({wire}, {dw}, {aw}, "");']
                    elif direction_is_manager(direction):
                        lines += [tab + f'`SB_AXIL_S({wire}, {dw}, {aw}, "");']
                    else:
                        raise Exception(f'Unsupported AXI-Lite direction: {direction}')
            elif type == 'gpio':
                if direction == 'input':
                    width = value['width']
                    new_wire = f'{instance}_input_{name}'
                    lines += [
                        tab + f'wire [{width-1}:0] {new_wire};',
                        tab + f'assign {new_wire} = {wire};'
                    ]
                    value['wire'] = new_wire
                else:
                    pass
            elif type == 'plusarg':
                width = value['width']

                plusarg = value['plusarg']
                assert plusarg is not None

                plusarg_wire = f'{wire}_plusarg'
                plusarg_width = 32  # TODO use long or another format?

                lines += [
                    tab + f'reg [{plusarg_width - 1}:0] {plusarg_wire} = {value["default"]};',
                    tab + 'initial begin',
                    2 * tab + f"void'($value$plusargs(\"{plusarg}=%d\", {plusarg_wire}));",
                    tab + 'end'
                ]

                lines += [tab + f'wire [{width - 1}:0] {wire};']

                if width <= plusarg_width:
                    lines += [tab + f'assign {wire} = {plusarg_wire}[{width - 1}:0];']
                else:
                    lines += [tab + f'assign {wire}[{plusarg_width - 1}:0] = {plusarg_wire};']
            else:
                raise Exception(f'Unsupported interface type: "{type}"')

            lines += ['']

    max_rst_dly = None

    for inst_resets in resets.values():
        if len(inst_resets) > 0:
            # find the max reset delay for this instance
            inst_max_rst_dly = max(reset['delay'] for reset in inst_resets)

            # update the overall max reset delay
            if (max_rst_dly is None) or (inst_max_rst_dly > max_rst_dly):
                max_rst_dly = inst_max_rst_dly

    if max_rst_dly is not None:
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

    for instance, module in instances.items():
        # start of the instantiation

        if len(parameters[instance]) > 0:
            lines += [tab + f'{module} #(']
            for n, (key, value) in enumerate(parameters[instance].items()):
                line = (2 * tab) + f'.{key}({value})'

                if n != len(parameters[instance]) - 1:
                    line += ','

                lines += [line]
            lines += [tab + f') {instance} (']
        else:
            lines += [tab + f'{module} {instance} (']

        connections = []

        # interfaces

        for name, value in interfaces[instance].items():
            type = value['type']
            wire = value['wire']

            if type_is_sb(type):
                assert wire is not None
                connections += [f'`SB_CONNECT({name}, {wire})']
            elif type_is_umi(type):
                if wire is None:
                    if value['direction'] == 'input':
                        connections += [f'`SB_TIEOFF_UMI_INPUT({name})']
                    elif value['direction'] == 'output':
                        connections += [f'`SB_TIEOFF_UMI_OUTPUT({name})']
                    else:
                        raise Exception(f'Unsupported UMI direction: {value["direction"]}')
                else:
                    connections += [f'`SB_UMI_CONNECT({name}, {wire})']
            elif type_is_axi(type):
                assert wire is not None
                connections += [f'`SB_AXI_CONNECT({name}, {wire})']
            elif type_is_axil(type):
                assert wire is not None
                connections += [f'`SB_AXIL_CONNECT({name}, {wire})']
            elif type_is_gpio(type) or type_is_plusarg(type):
                if wire is None:
                    # unused output
                    connections += [f'.{name}()']
                else:
                    connections += [f'.{name}({wire})']

        # clocks

        for clock in clocks[instance]:
            connections += [f'.{clock["name"]}(clk)']

        # resets

        for reset in resets[instance]:
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

        for key, value in tieoffs[instance].items():
            wire = value.get('wire')

            if wire is None:
                wire = ''

            connections += [f'.{key}({wire})']

        for n, connection in enumerate(connections):
            if n != len(connections) - 1:
                connection += ','
            lines += [(2 * tab) + connection]

        lines += [tab + ');']
        lines += ['']

    # initialize queue connections for this instance

    lines += [
        tab + 'string uri_sb_value;',
        '',
        tab + 'initial begin',
        (2 * tab) + '/* verilator lint_off IGNOREDRETURN */'
    ]

    for inst_interfaces in interfaces.values():
        for value in inst_interfaces.values():
            external = value['external']

            if not external:
                continue

            wire = value['wire']

            lines += [
                (2 * tab) + f'if($value$plusargs("{wire}=%s", uri_sb_value)) begin',
                (3 * tab) + f'{wire}_sb_inst.init(uri_sb_value);',
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


def direction_is_inout(direction):
    return direction.lower() in ['inout']


def direction_is_manager(direction):
    return direction.lower() in ['m', 'manager', 'master', 'indicator']


def direction_is_subordinate(direction):
    return direction.lower() in ['s', 'subordinate', 'slave', 'target']


def normalize_direction(type, direction):
    if type_is_const(type):
        if direction_is_output(direction):
            return 'output'
        else:
            raise Exception(f'Unsupported direction for interface type "{type}": "{direction}"')
    elif type_is_plusarg(type):
        if direction_is_input(direction):
            return 'input'
        else:
            raise Exception(f'Unsupported direction for interface type "{type}": "{direction}"')
    elif type_is_sb(type) or type_is_umi(type) or type_is_gpio(type):
        if direction_is_input(direction):
            return 'input'
        elif direction_is_output(direction):
            return 'output'
        elif direction_is_inout(direction):
            return 'inout'
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


def directions_are_compatible(type_a, a, type_b, b):
    a = normalize_direction(type_a, a)
    b = normalize_direction(type_b, b)

    if a == 'input':
        return b in ['output', 'inout']
    elif a == 'output':
        return b in ['input', 'inout']
    elif a == 'inout':
        return b in ['input', 'output', 'inout']
    elif a == 'manager':
        return b == 'subordinate'
    elif a == 'subordinate':
        return b == 'manager'
    else:
        raise Exception(f'Cannot determine if directions are compatible: {a} and {b}')


def types_are_compatible(a, b):
    a = normalize_intf_type(a)
    b = normalize_intf_type(b)

    if type_is_const(a):
        return type_is_gpio(b)
    elif type_is_const(b):
        return type_is_gpio(a)
    else:
        return a == b


def flip_intf(a):
    type = normalize_intf_type(a['type'])
    direction = normalize_direction(type=type, direction=a['direction'])

    retval = deepcopy(a)

    if type_is_sb(type) or type_is_umi(type):
        if direction == 'input':
            retval['direction'] = 'output'
        elif direction == 'output':
            retval['direction'] = 'input'
        else:
            raise Exception(f'Unsupported direction: {direction}')
    elif type_is_axi(type) or type_is_axil(type):
        if direction == 'manager':
            retval['direction'] = 'subordinate'
        elif direction == 'subordinate':
            retval['direction'] = 'manager'
        else:
            raise Exception(f'Unsupported direction: {direction}')
    else:
        raise Exception(f'Unsupported interface type: "{type}"')

    return retval


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


def type_is_input(type):
    return type.lower() in ['i', 'in', 'input']


def type_is_output(type):
    return type.lower() in ['o', 'out', 'output']


def type_is_gpio(type):
    return type.lower() in ['gpio']


def type_is_const(type):
    return type.lower() in ['const', 'constant']


def type_is_plusarg(type):
    return type.lower() in ['plusarg']


def normalize_intf_type(type):
    if type_is_sb(type):
        return 'sb'
    elif type_is_umi(type):
        return 'umi'
    elif type_is_axi(type):
        return 'axi'
    elif type_is_axil(type):
        return 'axil'
    elif type_is_input(type):
        return 'input'
    elif type_is_output(type):
        return 'output'
    elif type_is_gpio(type):
        return 'gpio'
    elif type_is_const(type):
        return 'const'
    elif type_is_plusarg(type):
        return 'plusarg'
    else:
        raise ValueError(f'Unsupported interface type: "{type}"')


def create_intf_objs(intf_defs, fresh=True, max_rate=-1):
    intf_objs = {}

    umi_txrx = {}

    for name, value in intf_defs.items():
        type = value['type']

        if type == 'plusarg':
            continue

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
