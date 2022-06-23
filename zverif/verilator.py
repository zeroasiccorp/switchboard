import ubelt
import shutil
from pathlib import Path
from doit.task import clean_targets

from zverif.utils import file_list

DEFAULT_TOP = 'zverif_top'
DEFAULT_VERILATOR = 'verilator'
DEFAULT_BUILD_DIR = Path('.') / 'build' / 'verilator'

def verilator_build_task(sources, top=DEFAULT_TOP, build_dir=None,
    name='verilator_build', **kwargs):

    # set defaults
    if build_dir is None:
        build_dir = DEFAULT_BUILD_DIR.resolve()

    # resolve patterns in source files
    sources = file_list(sources)

    return {
        'name': name,
        'file_dep': sources,
        'targets': [build_dir / 'obj_dir' / f'V{top}'],
        'actions': [(verilator_build, [], {
                'build_dir': build_dir,
                'top': top,
                'sources': sources
            } | kwargs)],
        'clean': [clean_targets,
            lambda: shutil.rmtree(build_dir, ignore_errors=True)],
        'doc': 'Build Verilator simulation binary.'
    }

def verilator_build(build_dir, top, sources):
    # create a fresh build directory
    shutil.rmtree(build_dir, ignore_errors=True)
    Path(build_dir).mkdir(exist_ok=True, parents=True)

    # convert Verilog to C
    verilate(build_dir=build_dir, top=top, sources=sources)

    # build simulation binary
    verilator_compile(build_dir=build_dir, top=top)

def verilate(top, sources, build_dir, verilator=DEFAULT_VERILATOR):
    # build up the command
    cmd = []
    cmd += [verilator]  # TODO make generic
    cmd += ['--top', top]  # TODO make generic
    cmd += ['-trace']  # TODO make generic
    cmd += ['-CFLAGS', '-Wno-unknown-warning-option']
    cmd += ['--cc']
    cmd += ['--exe']
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

def verilator_task(name, build_dir=DEFAULT_BUILD_DIR, top=DEFAULT_TOP,
    basename='verilator', files=None, **kwargs):

    if files is None:
        files = {}
    files = {k: Path(v).resolve() for k, v in files.items()}

    if build_dir is None:
        build_dir = DEFAULT_BUILD_DIR
    build_dir = Path(build_dir).resolve()

    file_dep = []
    file_dep += [build_dir / 'obj_dir' / f'V{top}']
    file_dep += list(files.values())

    return {
        'name': f'{basename}:{name}',
        'file_dep': file_dep,
        'actions': [(verilator, [], {
            'build_dir': build_dir,
            'top': top,
            'files': files
        } | kwargs)],
        'uptodate': [False]  # i.e., always run
    }

def verilator(build_dir, top, files, expect=None):
    # set defaults
    if expect is None:
        expect = []

    # build up the command
    cmd = []
    cmd += [build_dir / 'obj_dir' / f'V{top}']
    for k, v in files.items():
        cmd += [f'+{k}={v}']

    cmd = [str(elem) for elem in cmd]

    info = ubelt.cmd(cmd, tee=True, check=True)
    for e in expect:
        assert e in info['out'], f'Did not find "{e}" in output'
