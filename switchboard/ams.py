# Utilities for AMS simulation

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)


from pathlib import Path


def parse_spice_subckts(filename):
    subckts = []

    with open(filename, 'r') as f:
        contents = f.read()

    contents = contents.replace('\n+', ' ')

    for line in contents.split('\n'):
        line = line.strip().lower()

        if line.startswith('.subckt'):
            tokens = line.split()

            name = tokens[1]

            pins = []
            for pin in tokens[2:]:
                if pin == '.params':
                    break
                else:
                    pins.append(pin)

            subckts.append(dict(name=name, pins=pins))

    return subckts


def regularize_ams_input(input, vss=0.0, vdd=1.0, tr=5e-9, tf=5e-9):
    if len(input) == 1:
        return (input[0], vss, vdd, tr, tf)
    elif len(input) == 3:
        return (input[0], input[1], input[2], tr, tf)
    elif len(input) == 4:
        return (input[0], input[1], input[2], input[3], tf)
    elif len(input) == 5:
        return input
    else:
        raise ValueError(f'Unsupported input length: {len(input)}')


def make_ams_spice_wrapper(name, filename, inputs, outputs, dir, nl='\n'):
    text = []

    text += [f'* Spice wrapper for module "{name}"']

    # instantiate DUT

    subckts = parse_spice_subckts(filename)

    for subckt in subckts:
        if subckt['name'].lower() == name.lower():
            break
    else:
        raise Exception(f'Could not find subckt "{name}"')

    text += ['']
    text += [f'.INCLUDE "{Path(filename).resolve()}"']
    text += [' '.join(
        ['Xdut'] + [pin.lower() for pin in subckt['pins']] + [subckt['name'].lower()])]

    if len(inputs) > 0:
        inputs = [regularize_ams_input(input) for input in inputs]

        # consolidate DAC models

        dac_counter = 0
        dac_models = {}
        dac_mapping = {}

        for input in inputs:
            input_name = input[0].lower()
            tr = input[3]
            tf = input[4]

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

        for k, input in enumerate(inputs):
            output_name = input[0].lower()
            tr = input[3]
            tf = input[4]

            dac_model = dac_models[(tr, tf)]
            text += [f'YDAC A{output_name.upper()} {output_name} 0 {dac_model}']

    if len(outputs) > 0:
        text += ['']
        text += ['* Voltage outputs']

        for k, output in enumerate(outputs):
            output_name = output[0].lower()
            text += [f'.MEASURE TRAN a{output_name} EQN V({output_name})']

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

    ios += ['input clk']

    for input in inputs:
        ios += [f'input {input[0]}']

    for output in outputs:
        ios += [f'output {output[0]}']

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
        input_name = input[0]
        vol = input[1]
        voh = input[2]

        analog = f'A{input_name.upper()}'
        text += [
            '',
            tab + f'real {analog};',
            tab + f'always @({analog}) begin',
            tab + tab + f'x.put("{analog}", {analog});',
            tab + 'end',
            tab + f'assign {analog} = {input_name} ? {voh} : {vol};'
        ]

    if len(outputs) > 0:
        for output in outputs:
            output_name = output[0]
            analog = f'a{output_name.lower()}'
            text += [
                '',
                tab + f'real {analog};',
                tab + f'reg cmp_{analog};',
                tab + f'assign {output_name} = cmp_{analog};'
            ]

        text += [
            '',
            tab + 'always @(posedge clk) begin',
            tab + tab + '/* verilator lint_off BLKSEQ */'
        ]

        for output in outputs:
            output_name = output[0]
            vil = output[1]
            vih = output[2]

            analog = f'a{output_name.lower()}'
            cmp = f'cmp_{analog}'

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
