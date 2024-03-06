# Utilities for AMS simulation

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)


import re
from pathlib import Path


def parse_spice_subckts(filename):
    subckts = []

    with open(filename, 'r') as f:
        contents = f.read()

    # deal with line continuation
    contents = contents.replace('\n+', ' ')

    for line in contents.split('\n'):
        # example subcircuit definition
        # .SUBCKT CktName pin0 pin1 pin2 .PARAMS a=1.23 b=2.34

        line = line.strip().lower()

        if line.startswith('.subckt'):
            tokens = line.split()

            if len(tokens) < 2:
                # subcircuit definition is empty
                continue

            name = tokens[1]

            pins = []
            for pin in tokens[2:]:
                if pin == '.params':
                    break
                else:
                    pins.append(pin)

            subckts.append(dict(name=name, pins=pins))

    return subckts


def is_bus(name):
    return '[' in name


def split_apart_bus(signal):
    assert 'name' in signal, 'AMS signal must have a name.'

    # example: signalName[msb:lsb]

    name = signal['name']

    m = re.match(r'(.*)\[([0-9]+):([0-9]+)\]$', name)

    if m is not None:
        prefix = signal.copy()
        prefix['name'] = m.groups()[0]

        msb = int(m.groups()[1])
        lsb = int(m.groups()[2])

        retval = []

        for subsignal in split_apart_bus(prefix):
            for k in range(lsb, msb + 1):
                subsignal = signal.copy()
                subsignal['indices'] = subsignal['indices'] + (k,)
                retval.append(subsignal)

        return retval
    else:
        signal = signal.copy()
        signal['indices'] = ()
        return [signal]


def regularize_ams_input(input, vol=0.0, voh=1.0, tr=5e-9, tf=5e-9):
    assert 'name' in input, 'AMS input must have a name.'

    return {
        'name': input['name'],
        'vol': input.get('vol', vol),
        'voh': input.get('voh', voh),
        'tr': input.get('tr', tr),
        'tf': input.get('tf', tf),
        'indices': input.get('indices', ())
    }


def regularize_ams_output(output, vil=0.2, vih=0.8):
    assert 'name' in output, 'AMS output must have a name.'

    return {
        'name': output['name'],
        'vil': output.get('vil', vil),
        'vih': output.get('vih', vih),
        'indices': output.get('indices', ())
    }


def regularize_ams_inputs(inputs, **kwargs):
    return [
        regularize_ams_input(subinput, **kwargs)
        for input in inputs
        for subinput in split_apart_bus(input)
    ]


def regularize_ams_outputs(outputs, **kwargs):
    return [
        regularize_ams_output(suboutput, **kwargs)
        for output in outputs
        for suboutput in split_apart_bus(output)
    ]


def spice_ext_name(signal):
    return signal['name'] + ''.join(f'[{i}]' for i in signal['indices'])


def spice_int_name(signal):
    return signal['name'] + ''.join(f'_{i}_' for i in signal['indices'])


def vlog_ext_name(signal):
    return signal['name'] + ''.join(f'[{i}]' for i in signal['indices'])


def vlog_int_name(signal):
    return signal['name'] + ''.join(f'_{i}_' for i in signal['indices'])


def make_ams_spice_wrapper(name, filename, inputs, outputs, dir, nl='\n'):
    text = []

    text += [f'* SPICE wrapper for module "{name}"']

    # instantiate DUT

    subckts = parse_spice_subckts(filename)

    for subckt in subckts:
        if subckt['name'].lower() == name.lower():
            break
    else:
        raise Exception(f'Could not find subckt "{name}"')

    text += [
        '',
        f'*** Start of file "{Path(filename).resolve()}"',
        ''
    ]

    with open(filename) as f:
        subcircuit_definition = f.read().splitlines()

    text += subcircuit_definition

    text += [
        '',
        f'*** End of file "{Path(filename).resolve()}"',
        ''
    ]

    text += [' '.join(
        ['Xdut'] + [pin.lower() for pin in subckt['pins']] + [subckt['name'].lower()])]

    if len(inputs) > 0:
        inputs = regularize_ams_inputs(inputs)

        # consolidate DAC models

        dac_counter = 0
        dac_models = {}
        dac_mapping = {}

        for input in inputs:
            input_name = spice_ext_name(input)
            tr = input['tr']
            tf = input['tf']

            text += ['']
            text += ['* DAC models']

            if (tr, tf) not in dac_models:
                dac_name = f'amsDac{dac_counter}'
                text += [f'.model {dac_name} DAC (tr={tr} tf={tf})']
                dac_models[(tr, tf)] = dac_name
                dac_counter += 1
            else:
                dac_name = dac_models[(tr, tf)]

            dac_mapping[input_name] = dac_name

        text += ['']
        text += ['* Voltage inputs']

        for input in inputs:
            int_name = spice_int_name(input)
            ext_name = spice_ext_name(input)
            tr = input['tr']
            tf = input['tf']

            dac_model = dac_models[(tr, tf)]
            text += [f'YDAC SB_DAC_{int_name.upper()} {ext_name} 0 {dac_model}']

    if len(outputs) > 0:
        text += ['']
        text += ['* Voltage outputs']

        outputs = regularize_ams_outputs(outputs)

        for output in outputs:
            int_name = spice_int_name(output)
            ext_name = spice_ext_name(output)
            text += [f'.MEASURE TRAN SB_ADC_{int_name.upper()} EQN V({ext_name})']

    text += ['']
    text += ['.TRAN 0 1']

    text += ['']
    text += ['.END']

    text = nl.join(text)

    outfile = Path(dir) / f'{name}.wrapper.cir'

    with open(outfile, 'w') as f:
        f.write(text)

    return outfile.resolve()


def make_ams_verilog_wrapper(name, filename, inputs, outputs, dir, nl='\n', tab='    '):
    text = []

    text += [f'// Verilog wrapper for module "{name}"']

    text += ['']
    text += [f'module {name} (']

    ios = []

    ios += ['input SB_CLK']

    for input in inputs:
        ios += [f'input {input["name"]}']

    for output in outputs:
        ios += [f'output {output["name"]}']

    inputs = regularize_ams_inputs(inputs)
    outputs = regularize_ams_outputs(outputs)

    ios = [tab + io for io in ios]
    ios = [io + ',' for io in ios[:-1]] + [ios[-1]]

    text += ios

    text += [');']

    text += [
        tab + 'xyce_intf x ();',
        '',
        tab + 'initial begin',
        tab + tab + f'x.init("{filename}");',
        tab + 'end'
    ]

    for input in inputs:
        int_name = vlog_int_name(input)
        ext_name = vlog_ext_name(input)

        vol = input['vol']
        voh = input['voh']

        analog = f'SB_DAC_{int_name.upper()}'
        text += [
            '',
            tab + f'real {analog};',
            tab + f'always @({analog}) begin',
            tab + tab + f'x.put("{analog.upper()}", {analog});',
            tab + 'end',
            tab + f'assign {analog} = {ext_name} ? {voh} : {vol};'
        ]

    if len(outputs) > 0:
        for output in outputs:
            int_name = vlog_int_name(output)
            ext_name = vlog_ext_name(output)

            analog = f'SB_ADC_{int_name.upper()}'
            cmp = f'SB_CMP_{int_name.upper()}'

            text += [
                '',
                tab + f'real {analog};',
                tab + f'reg {cmp};',
                tab + f'assign {ext_name} = {cmp};'
            ]

        text += [
            '',
            tab + 'always @(posedge SB_CLK) begin',
            tab + tab + '/* verilator lint_off BLKSEQ */'
        ]

        for output in outputs:
            int_name = vlog_int_name(output)

            vil = output['vil']
            vih = output['vih']

            analog = f'SB_ADC_{int_name.upper()}'
            cmp = f'SB_CMP_{int_name.upper()}'

            text += [
                tab + tab + f'x.get("{analog}", {analog});',
                tab + tab + f'if ({analog} >= {vih}) begin',
                tab + tab + tab + f'{cmp} = 1;',
                tab + tab + f'end else if ({analog} <= {vil}) begin',
                tab + tab + tab + f'{cmp} = 0;',
                tab + tab + 'end'
            ]

        text += [
            tab + tab + '/* verilator lint_on BLKSEQ */',
            tab + 'end'
        ]

    text += ['endmodule']

    text = nl.join(text)

    outfile = Path(dir) / f'{name}.wrapper.sv'

    with open(outfile, 'w') as f:
        f.write(text)

    return outfile.resolve()
