# Utilities for AMS simulation

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)


import re
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path


def parse_spice_subckts(filename: str) -> List[Dict[str, Any]]:
    """
    Reads the contents of a SPICE file and returns a list of the subcircuit
    definitions that are found.  Parsing capability is currently limited and
    does not take into account .INCLUDE statements.

    Parameters
    ----------
    filename: str
        The path of the file to read from.

    Returns
    -------
    list of dictionaries
        A list of dictionaries, each representing a SPICE subcircuit.  The keys
        in each dictionary are "name" and "pins".  The "name" key maps to a
        string that contains the name of the circuit, while "pins" maps to a
        list of strings, each representing a pin in the subcircuit.  The order
        of pins in that list matches the order in the subcircuit definition.
    """

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


def parse_bus(name: str) -> Optional[Tuple[str, int, int]]:
    """
    Tries to parse a signal name as a bus, returning a tuple representing
    the bus: (signalName, msb, lsb).  If the signal name isn't a bus, the
    function returns None.

    Example:
    parse_bus("mySignal[42:34]") -> ("mySignal", 42, 34)
    parse_bus("anotherSignal") -> None

    Parameters
    ----------
    name: str
        The signal name to parse.

    Returns
    -------
    tuple with three values, or None
        A tuple with three values: (signalName, msb, lsb).  "signalName" is a
        string, while "msb" and "lsb" are integers.  If the provided signal
        name isn't a bus, the function returns None.
    """

    # example: signalName[msb:lsb] -> returns (signalName, msb, lsb)

    matches = re.match(r'(\w+)\[(\d+):(\d+)\]', name)

    if matches is not None:
        groups = matches.groups()

        prefix = groups[0]
        msb = int(groups[1])
        lsb = int(groups[2])

        return (prefix, msb, lsb)
    else:
        return None


def split_apart_bus(signal: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Converts a dictionary representing a signal into a list of signals,
    each representing one bit in the bus.  If the signal isn't a bus,
    the function returns a list with one element, the original signal.

    Parameters
    ----------
    signal: Dict[str, Any]
        The signal to split apart into bits.

    Returns
    -------
    list of dictionaries
        A list of dictionaries, with each dictionary representing a
        single bit in the bus.  The format of each of these dictionaries
        is the same as the format of the dictionary provided as input.
    """

    assert 'name' in signal, 'AMS signal must have a name.'

    name = signal['name']

    bus = parse_bus(name)

    if bus is not None:
        prefix, msb, lsb = bus

        retval = []

        for k in range(lsb, msb + 1):
            subsignal = signal.copy()
            subsignal['name'] = prefix
            subsignal['index'] = k
            if signal.get('initial', None) is not None:
                subsignal['initial'] = (signal['initial'] >> k) & 1
            retval.append(subsignal)

        return retval
    else:
        signal = signal.copy()
        signal['index'] = None
        return [signal]


def regularize_ams_input(
    input: Dict[str, Any],
    vol: float = 0.0,
    voh: float = 1.0,
    tr: float = 5e-9,
    tf: float = 5e-9
) -> Dict[str, Any]:
    """
    Fills in missing values in a dictionary representing an input signal.

    Parameters
    ----------
    input: Dict[str, Any]
        The signal to regularize.
    vol: float
        Default real-number voltage to pass to the SPICE subcircuit input
        when the digital value provided is "0".  If already defined in
        "input", this argument is ignored.
    voh: float
        Default real-number voltage to pass to the SPICE subcircuit input
        when the digital value provided is "1".  If already defined in
        "input", this argument is ignored.
    tr: float
        Default time taken in the SPICE simulation to transition from a low
        value to a high value.  If already defined in "input", this argument
        is ignored.
    tf: float
        Default time taken in the SPICE simulation to transition from a high
        value to a low value.  If already defined in "input", this argument
        is ignored.

    Returns
    -------
    dictionary
        A dictionary with missing values filled in with defaults.
    """

    assert 'name' in input, 'AMS input must have a name.'

    return {
        'name': input['name'],
        'vol': input.get('vol', vol),
        'voh': input.get('voh', voh),
        'tr': input.get('tr', tr),
        'tf': input.get('tf', tf),
        'index': input.get('index', None)
    }


def regularize_ams_output(output: str, vil: float = 0.2, vih: float = 0.8):
    """
    Fills in missing values in a dictionary representing an output signal.

    Parameters
    ----------
    output: Dict[str, Any]
        The signal to regularize.
    vil: float
        Default low voltage threshold, below which the real-number voltage
        from the SPICE simulation is considered to be a logical "0".  If
        already defined in "output", this argument is ignored.
    vih: float
        Default high voltage threshold, above which the real-number voltage
        from the SPICE simulation is considered to be a logical "1".  If
        already defined in "output", this argument is ignored.

    Returns
    -------
    dictionary
        A dictionary with missing values filled in with defaults.
    """

    assert 'name' in output, 'AMS output must have a name.'

    return {
        'name': output['name'],
        'vil': output.get('vil', vil),
        'vih': output.get('vih', vih),
        'initial': output.get('initial', None),
        'index': output.get('index', None)
    }


def regularize_ams_inputs(inputs: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
    """
    Fills in missing values in a list of signals, splitting apart buses into
    individual bits as they are encountered.

    Parameters
    ----------
    inputs: List[Dict[str, Any]]
        List of signals, represented as dictionaries.

    Returns
    -------
    list of dictionaries
        List of signals, represented as dictionaries.
    """

    return [
        regularize_ams_input(subinput, **kwargs)
        for input in inputs
        for subinput in split_apart_bus(input)
    ]


def regularize_ams_outputs(outputs: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
    """
    Fills in missing values in a list of signals, splitting apart buses into
    individual bits as they are encountered.

    Parameters
    ----------
    outputs: List[Dict[str, Any]]
        List of signals, represented as dictionaries.

    Returns
    -------
    list of dictionaries
        List of signals, represented as dictionaries.
    """

    return [
        regularize_ams_output(suboutput, **kwargs)
        for output in outputs
        for suboutput in split_apart_bus(output)
    ]


def spice_ext_name(signal: Dict[str, Any]) -> str:
    """
    Returns the name of a signal as it should be referenced as
    a port on a SPICE subcircuit.

    Parameters
    ----------
    signal: Dict[str, Any]
        Signal represented as a dictionary

    Returns
    -------
    string
        Signal name to be used in a SPICE file.
    """

    if signal['index'] is None:
        return signal['name']
    else:
        return f'{signal["name"]}[{signal["index"]}]'


def spice_int_name(signal: Dict[str, Any]) -> str:
    """
    Returns the name of a signal as it should be referenced as
    a signal within a SPICE subcircuit, avoiding special bus
    characters.

    Parameters
    ----------
    signal: Dict[str, Any]
        Signal represented as a dictionary

    Returns
    -------
    string
        Signal name to be used in a SPICE file.
    """

    if signal['index'] is None:
        return signal['name']
    else:
        return f'{signal["name"]}_IDX_{signal["index"]}'


def vlog_ext_name(signal: Dict[str, Any]) -> str:
    """
    Returns the name of a signal as it should be referenced as
    a port on a Verilog module.

    Parameters
    ----------
    signal: Dict[str, Any]
        Signal represented as a dictionary

    Returns
    -------
    string
        Signal name to be used in a Verilog file.
    """

    if signal['index'] is None:
        return signal['name']
    else:
        return f'{signal["name"]}[{signal["index"]}]'


def vlog_int_name(signal: Dict[str, Any]) -> str:
    """
    Returns the name of a signal as it should be referenced as
    a signal within a Verilog module, avoiding special bus
    characters.

    Parameters
    ----------
    signal: Dict[str, Any]
        Signal represented as a dictionary

    Returns
    -------
    string
        Signal name to be used in a Verilog file.
    """

    if signal['index'] is None:
        return signal['name']
    else:
        return f'{signal["name"]}_IDX_{signal["index"]}'


def make_ams_spice_wrapper(
    name: str,
    filename: str,
    pins: List[Dict[str, Any]],
    dir: str,
    nl: str = '\n'
):
    """
    Writes a SPICE file that wraps the SPICE subcircuit defined in filename.
    The wrapper contains ADCs and DACs for interaction between a Verilog
    simulation and SPICE simulation.

    Parameters
    ----------
    name: str
        Name of the SPICE subcircuit to be wrapped
    filename: str
        Path to the file where the SPICE subcircuit is defined
    pins: List[Dict[str, Any]]
        List of pins on the SPICE subcircuit, each represented as a dictionary.
    dir: str
        Path to the directory where the SPICE wrapper should be written.
    nl: str
        String/character to be used for indicating newlines.
    """

    # split apart pins into inputs, outputs, and constants

    inputs = [pin for pin in pins if pin.get('type', None) == 'input']
    outputs = [pin for pin in pins if pin.get('type', None) == 'output']
    constants = [pin for pin in pins if pin.get('type', None) == 'constant']

    # start building up the wrapper text

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

        text += ['']
        text += ['* DAC models']

        for input in inputs:
            input_name = spice_ext_name(input)
            tr = input['tr']
            tf = input['tf']

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

    if len(constants) > 0:
        text += ['']
        text += ['* Constant signals']

        for constant in constants:
            const_name = constant['name']
            value = constant['value']
            text += [f'V{const_name} {const_name} 0 {value}']

    text += ['']
    text += ['.TRAN 0 1']

    text += ['']
    text += ['.END']

    text = nl.join(text)

    outfile = Path(dir) / f'{name}.wrapper.cir'

    with open(outfile, 'w') as f:
        f.write(text)

    return outfile.resolve()


def make_ams_verilog_wrapper(
    name: str,
    filename: str,
    pins: List[Dict[str, Any]],
    dir: str,
    nl: str = '\n',
    tab: str = '    '
):
    """
    Writes a Verilog file that contains a module definition matching the SPICE
    subcircuit in the provided file.  The module definition uses VPI/DPI to
    interact with the Xyce.

    Parameters
    ----------
    name: str
        Name of the SPICE subcircuit to be wrapped
    filename: str
        Path to the file where the SPICE subcircuit is defined
    pins: List[Dict[str, Any]]
        List of pins on the SPICE subcircuit, each represented as a dictionary.
    dir: str
        Path to the directory where the SPICE wrapper should be written.
    nl: str
        String/character to be used to for indicating newlines.
    nl: str
        String/character to be used for tabs.
    """

    # start building up the wrapper text

    text = []

    text += [f'// Verilog wrapper for module "{name}"']

    text += ['']
    text += [f'module {name} (']

    ios = []

    for pin in pins:
        type = pin.get('type', None)
        if type in {'input', 'output'}:
            pin_name = pin['name']

            bus = parse_bus(pin_name)

            if bus is not None:
                prefix, msb, lsb = bus
                ios += [f'{type} [{msb}:{lsb}] {prefix}']
            else:
                ios += [f'{type} {pin_name}']

    ios += ['input SB_CLK']

    # split apart pins into inputs and outputs.  constants are ignored here,
    # since they are tied off in the spice netlist

    inputs = [pin for pin in pins if pin.get('type', None) == 'input']
    outputs = [pin for pin in pins if pin.get('type', None) == 'output']

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

            if output.get('initial', None) is not None:
                initial = f" = 1'b{output['initial']}"
            else:
                initial = ''

            text += [
                '',
                tab + f'real {analog};',
                tab + f'reg {cmp}{initial};',
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
