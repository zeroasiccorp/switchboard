import ubelt

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