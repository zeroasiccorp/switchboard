from os import link
import ubelt
from pathlib import Path
from zverif.makehex import makehex
from zverif.utils import file_list
#from zverif.utils import get_gcc_deps

DEFAULT_RISCV_PREFIX = 'riscv64-unknown-elf-'
DEFAULT_RISCV_ABI = 'ilp32'
DEFAULT_RISCV_ISA = 'rv32im'
DEFAULT_RISCV_GCC = f'{DEFAULT_RISCV_PREFIX}gcc'
DEFAULT_RISCV_OBJCOPY = f'{DEFAULT_RISCV_PREFIX}objcopy'
DEFAULT_BUILD_DIR = Path('.') / 'build' / 'sw'

def riscv_elf_task(name, sources=None, linker_script=None,
    include_paths=None, output=None, basename='elf', **kwargs):
    
    # pre-process arguments
    
    sources = file_list(sources)
    include_paths = file_list(include_paths)

    if linker_script is not None:
        linker_script = file_list(linker_script)
        assert len(linker_script) == 1, f'Need exactly one linker script, found {len(linker_script)}.'
        linker_script = linker_script[0]

    if output is None:
        output = (DEFAULT_BUILD_DIR / f'{name}.elf').resolve()
    output = Path(output)

    # determine file dependencies

    file_dep = []

    file_dep += sources
    if linker_script is not None:
        file_dep += [linker_script]

    return {
        'name': f'{basename}:{name}',
        'file_dep': file_dep,
        'targets': [output],
        'actions': [(build_elf, [], {
            'sources': sources,
            'include_paths': include_paths,
            'linker_script': linker_script,
            'output': output
        } | kwargs)],
        'clean': True
    }

def build_elf(sources, linker_script, include_paths, output,
    isa=DEFAULT_RISCV_ISA, abi=DEFAULT_RISCV_ABI, gcc=DEFAULT_RISCV_GCC):

    # create the build directory if needed
    Path(output).parent.mkdir(exist_ok=True, parents=True)

    # build up the command
    cmd = []
    cmd += [gcc]
    cmd += [f'-mabi={abi}']
    cmd += [f'-march={isa}']
    cmd += ['-static']
    cmd += ['-mcmodel=medany']
    cmd += ['-fvisibility=hidden']
    cmd += ['-nostdlib']
    cmd += ['-nostartfiles']
    cmd += ['-fno-builtin']
    cmd += [f'-T{linker_script}']
    cmd += sources
    cmd += [f'-I{elem}' for elem in include_paths]
    cmd += ['-o', output]

    cmd = [str(elem) for elem in cmd]

    info = ubelt.cmd(cmd, tee=True, check=True)

def riscv_bin_task(name, input=None, output=None, basename='bin', **kwargs):
    # preprocess inputs

    if input is None:
        input = (DEFAULT_BUILD_DIR / f'{name}.elf')
    input = Path(input).resolve()

    if output is None:
        output = input.with_suffix('.bin')
    output = Path(output).resolve()

    return {
        'name': f'{basename}:{name}',
        'file_dep': [input],
        'targets': [output],
        'actions': [(build_bin, [], {
                'input': input,
                'output': output
            } | kwargs)],
        'clean': True
    }

def build_bin(input, output, objcopy=DEFAULT_RISCV_OBJCOPY):
    # build up the command
    cmd = []
    cmd += [objcopy]
    cmd += ['-O', 'binary']
    cmd += [input]
    cmd += [output]

    cmd = [str(elem) for elem in cmd]

    info = ubelt.cmd(cmd, tee=True, check=True)

def hex_task(name, input=None, output=None, basename='hex', **kwargs):
    # preprocess inputs

    if input is None:
        input = (DEFAULT_BUILD_DIR / f'{name}.bin')
    input = Path(input).resolve()

    if output is None:
        output = input.with_suffix('.hex')
    output = Path(output).resolve()

    return {
        'name': f'{basename}:{name}',
        'file_dep': [input],
        'targets': [output],
        'actions': [(makehex, [], {
                'input': input,
                'output': output
            } | kwargs)],
        'clean': True
    }
