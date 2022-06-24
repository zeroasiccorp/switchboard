from os import link
import ubelt
from pathlib import Path
from zverif.makehex import makehex
from zverif.utils import file_list, add_task
from zverif.config import ZvConfig

CFG = ZvConfig()

def add_riscv_elf_task(tasks, name, sources=None, linker_script=None,
    include_paths=None, output=None, basename='elf', **kwargs):
    
    # pre-process arguments
    
    sources = file_list(sources)
    include_paths = file_list(include_paths)

    if linker_script is not None:
        linker_script = file_list(linker_script)
        assert len(linker_script) == 1, f'Need exactly one linker script, found {len(linker_script)}.'
        linker_script = linker_script[0]

    if output is None:
        output = (Path(CFG.sw_dir) / f'{name}.elf').resolve()
    output = Path(output)

    # determine file dependencies

    file_dep = []

    file_dep += sources
    if linker_script is not None:
        file_dep += [linker_script]

    task = {
        'name': name,
        'file_dep': file_dep,
        'targets': [output],
        'actions': [(build_elf, [], dict({
            'sources': sources,
            'include_paths': include_paths,
            'linker_script': linker_script,
            'output': output
        }, **kwargs))],
        'clean': True
    }
    add_task(task=task, tasks=tasks, basename=basename,
        doc='Build software ELF files.')

def build_elf(sources, linker_script, include_paths, output,
    isa=CFG.riscv_isa, abi=CFG.riscv_abi, gcc=CFG.riscv_gcc):

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

def add_riscv_bin_task(tasks, name, input=None, output=None, basename='bin', **kwargs):
    # preprocess inputs

    if input is None:
        input = (Path(CFG.sw_dir) / f'{name}.elf')
    input = Path(input).resolve()

    if output is None:
        output = input.with_suffix('.bin')
    output = Path(output).resolve()

    task = {
        'name': name,
        'file_dep': [input],
        'targets': [output],
        'actions': [(build_bin, [], dict({
                'input': input,
                'output': output
            }, **kwargs))],
        'clean': True
    }
    add_task(task=task, tasks=tasks, basename=basename,
        doc='Build software BIN files.')

def build_bin(input, output, objcopy=CFG.riscv_objcopy):
    # build up the command
    cmd = []
    cmd += [objcopy]
    cmd += ['-O', 'binary']
    cmd += [input]
    cmd += [output]

    cmd = [str(elem) for elem in cmd]

    info = ubelt.cmd(cmd, tee=True, check=True)

def add_hex_task(tasks, name, input=None, output=None, basename='hex', **kwargs):
    # preprocess inputs

    if input is None:
        input = (Path(CFG.sw_dir) / f'{name}.bin')
    input = Path(input).resolve()

    if output is None:
        output = input.with_suffix('.hex')
    output = Path(output).resolve()

    task = {
        'name': name,
        'file_dep': [input],
        'targets': [output],
        'actions': [(makehex, [], dict({
                'input': input,
                'output': output
            }, **kwargs))],
        'clean': True
    }
    add_task(task=task, tasks=tasks, basename=basename,
        doc='Build software HEX files.')
