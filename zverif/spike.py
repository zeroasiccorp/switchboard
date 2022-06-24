import ubelt
import sys
from pathlib import Path

from zverif.utils import file_list, add_task, calc_task_name, add_calc_dep_task
from zverif.config import ZvConfig

CFG = ZvConfig()

def add_spike_plugin_task(tasks, name, sources=None, include_paths=None,
    output=None, basename='spike_plugin', gcc=CFG.gcc, **kwargs):
    
    # pre-process arguments
    
    sources = file_list(sources)
    include_paths = file_list(include_paths)
    if output is None:
        output = (Path(CFG.spike_dir) / f'{name}.so').resolve()
    output = Path(output)

    # create task

    task = {
        'name': name,
        'calc_dep': [calc_task_name('_calc_dep', calc_task_name(basename, name))],
        'targets': [output],
        'actions': [(build_spike_plugin, [], dict({
            'sources': sources,
            'include_paths': include_paths,
            'output': output,
            'gcc': gcc
        }, **kwargs))],
        'clean': True
    }
    add_calc_dep_task(name=task['calc_dep'][0], tasks=tasks, sources=sources,
        include_paths=include_paths, gcc=gcc)
    add_task(task=task, tasks=tasks, basename=basename,
        doc='Build Spike plugins.')

def build_spike_plugin(sources, include_paths, output, gcc):
    # create the build directory if needed
    Path(output).parent.mkdir(exist_ok=True, parents=True)

    # build up the command
    cmd = []
    cmd += [gcc]
    if sys.platform == 'darwin':
        cmd += ['-bundle']
        cmd += ['-undefined', 'dynamic_lookup']
    else:
        cmd += ['-shared']
    cmd += ['-Wall']
    cmd += ['-Werror']
    cmd += ['-fPIC']
    cmd += sources
    cmd += [f'-I{elem}' for elem in include_paths]
    cmd += ['-o', output]

    cmd = [str(elem) for elem in cmd]

    info = ubelt.cmd(cmd, tee=True, check=True)

def add_spike_task(tasks, name, elf=None, plugins=None, basename='spike', **kwargs):
    # set defaults
    if elf is None:
        elf = (Path(CFG.sw_dir) / f'{name}.elf').resolve()
    if plugins is None:
        plugins = {}
    plugins = {str(Path(k).resolve()): v for k, v in plugins.items()}

    file_dep = list(plugins.keys()) + [elf]

    task = {
        'name': name,
        'file_dep': file_dep,
        'actions': [(run_spike, [], dict({
                'elf': elf,
                'plugins': plugins
            }, **kwargs))],
        'uptodate': [False],  # i.e., always run
    }
    add_task(task=task, tasks=tasks, basename=basename,
        doc='Run Spike emulation.')

def run_spike(elf, plugins, expect=None, isa=CFG.riscv_isa, spike=CFG.spike):
    # set defaults
    if expect is None:
        expect = []

    # build up the command
    cmd = []
    cmd += [spike]
    cmd += ['-m1']  # TODO make generic
    cmd += ['--isa', isa]
    for key, val in plugins.items():
        cmd += ['--extlib', key]
        cmd += [f'--device={Path(key).stem},{hex(val)}']
    cmd += [elf]

    cmd = [str(elem) for elem in cmd]

    info = ubelt.cmd(cmd, tee=True, check=True)
    for e in expect:
        assert e in info['out'], f'Did not find "{e}" in output'
