import glob
import ubelt

from typing import Dict
from doit.task import Task, dict_to_task
from pathlib import Path

def file_list(file_or_files, convert_to_path=True, resolve=True):
    if file_or_files is None:
        retval = []
    if isinstance(file_or_files, (str, Path)):
        retval = glob.glob(str(file_or_files))
        if convert_to_path:
            retval = [Path(file) for file in retval]
            if resolve:
                retval = [file.resolve() for file in retval]
    else:
        retval = []
        for file in file_or_files:
            retval += file_list(file, convert_to_path=convert_to_path, resolve=resolve)

    return retval

def run_gcc_for_deps(sources=None, include_dirs=None, gcc='gcc'):
    # set defaults
    if sources is None:
        sources = []
    if include_dirs is None:
        include_dirs = []

    # build up the command
    cmd = []
    cmd += [gcc]
    cmd += ['-M']
    cmd += sources
    cmd += [f'-I{elem}' for elem in include_dirs]
    cmd = [str(elem) for elem in cmd]

    # run the command
    info = ubelt.cmd(cmd, check=True)

    # return output of the command
    return info['out']

def get_gcc_deps(sources=None, include_dirs=None, gcc='gcc'):
    # get gcc output
    out = run_gcc_for_deps(sources=sources, include_dirs=include_dirs, gcc=gcc)

    # undo line continuation
    out = out.replace('\\\n', '')

    # split on whitespace
    out = out.split()

    # remove make target
    out = out[1:]

    # ignore empty strings
    out = [elem for elem in out if elem != '']

    return out

def calc_task_name(basename=None, name=None):
    if basename is None:
        if name is None:
            raise Exception('Need to provide a basename or name (or both)')
        else:
            return f'{name}'
    else:
        if name is None:
            return f'{basename}'
        else:
            return f'{basename}:{name}'

def add_task(task: dict, tasks: Dict[str, Task], basename: str=None, doc: str=None):
    # convert task to a Task object
    task['name'] = calc_task_name(basename=basename, name=task['name'])
    task = dict_to_task(task)

    # add task to dictionary of tasks
    tasks[task.name] = task

    # associate with a group task if needed
    if basename is not None:
        if basename not in tasks:
            tasks[basename] = Task(basename, None, doc=doc, has_subtask=True)
        tasks[basename].task_dep.append(task.name)
        task.subtask_of = basename
