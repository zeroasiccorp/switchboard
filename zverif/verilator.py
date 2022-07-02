import ubelt
import shutil
from pathlib import Path
from doit.task import clean_targets

from zverif.utils import file_list, add_task
from zverif.config import ZvConfig

CFG = ZvConfig()

def add_verilator_build_task(tasks, sources, top=CFG.rtl_top,
    build_dir=None, name='verilator_build', **kwargs):

    # set defaults
    if build_dir is None:
        build_dir = Path(CFG.verilator_dir).resolve()

    # resolve patterns in source files
    sources = file_list(sources)

    task = {
        'name': name,
        'file_dep': sources,
        'targets': [build_dir / 'obj_dir' / f'V{top}'],
        'actions': [(verilator_build, [], dict({
                'build_dir': build_dir,
                'top': top,
                'sources': sources
            }, **kwargs))],
        'clean': [clean_targets,
            lambda: shutil.rmtree(build_dir, ignore_errors=True)],
        'doc': 'Build Verilator simulation binary.'
    }
    add_task(task=task, tasks=tasks)

def verilator_build(build_dir, top, sources, libs=None):
    # set defaults
    if libs is None:
        libs = []

    # create a fresh build directory
    shutil.rmtree(build_dir, ignore_errors=True)
    Path(build_dir).mkdir(exist_ok=True, parents=True)

    # convert Verilog to C
    verilate(build_dir=build_dir, top=top, sources=sources, libs=libs)

    # build simulation binary
    verilator_compile(build_dir=build_dir, top=top)

def verilate(top, sources, build_dir, libs, verilator=CFG.verilator, timescale='1ns/1ps'):
    # build up the command
    cmd = []
    cmd += [verilator]
    cmd += ['--top-module', top]  # "--top" isn't supported on older versions...
    cmd += ['-trace']  # TODO make generic
    CFLAGS = []
    CFLAGS += ['-Wno-unknown-warning-option']
    if len(CFLAGS) > 0:
        cmd += ['-CFLAGS', ' '.join(CFLAGS)]
    LDFLAGS = []
    for lib in libs:
        LDFLAGS += [f'-l{lib}']
    if len(LDFLAGS) > 0:
        cmd += ['-LDFLAGS', ' '.join(LDFLAGS)]
    cmd += ['--cc']
    cmd += ['--exe']
    if timescale is not None:
        cmd += ['--timescale', timescale]
    cmd += sources

    cmd = [str(elem) for elem in cmd]

    info = ubelt.cmd(cmd, tee=True, check=True, cwd=build_dir)

def verilator_compile(build_dir, top):
    cmd = []
    cmd += ['make']
    cmd += ['-C', 'obj_dir']
    cmd += ['-j']
    cmd += ['-f', f'V{top}.mk']
    cmd += [f'V{top}']

    cmd = [str(elem) for elem in cmd]

    info = ubelt.cmd(cmd, tee=True, check=True, cwd=build_dir)

def add_verilator_task(tasks, build_dir=CFG.verilator_dir,
    top=CFG.rtl_top, name='verilator', **kwargs):

    build_dir = Path(build_dir).resolve()

    file_dep = []
    file_dep += [build_dir / 'obj_dir' / f'V{top}']

    task = {
        'name': name,
        'file_dep': file_dep,
        'actions': [(verilator, [], dict({
            'build_dir': build_dir,
            'top': top
        }, **kwargs))],
        'uptodate': [False]  # i.e., always run
    }
    add_task(task=task, tasks=tasks, doc='Run Verilator simulation.')

def verilator(build_dir, top):
    # build up the command
    cmd = []
    cmd += [build_dir / 'obj_dir' / f'V{top}']
    #cmd += ['+vcd']

    cmd = [str(elem) for elem in cmd]

    info = ubelt.cmd(cmd, tee=True, check=True)
