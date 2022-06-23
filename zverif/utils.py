import glob
from pathlib import Path
import ubelt

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