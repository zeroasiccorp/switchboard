# General utilities for working with switchboard

# Copyright (c) 2023 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

import atexit
import signal
import subprocess
import shlex


def plusargs_to_args(plusargs):
    args = []
    if plusargs is not None:
        if not isinstance(plusargs, list):
            raise TypeError('plusargs must be a list')
        for plusarg in plusargs:
            if isinstance(plusarg, (list, tuple)):
                if len(plusarg) != 2:
                    raise ValueError('Only lists/tuples of length 2 allowed')
                args += [f'+{plusarg[0]}={plusarg[1]}']
            else:
                args += [f'+{plusarg}']
    return args


def binary_run(bin, args=None, stop_timeout=10, use_sigint=False,
    quiet=False, print_command=False):

    cmd = []

    cmd += [bin]

    if args is not None:
        if not isinstance(args, list):
            raise TypeError('args must be a list')
        cmd += args

    cmd = [str(elem) for elem in cmd]
    if print_command:
        print(' '.join([shlex.quote(elem) for elem in cmd]))

    kwargs = {}
    if quiet:
        kwargs['stdout'] = subprocess.DEVNULL
        kwargs['stderr'] = subprocess.DEVNULL

    p = subprocess.Popen(cmd, **kwargs)

    def stop_bin(p=p, stop_timeout=stop_timeout, use_sigint=use_sigint):
        poll = p.poll()
        if poll is not None:
            # process has stopped
            return

        if use_sigint:
            try:
                p.send_signal(signal.SIGINT)
                p.wait(stop_timeout)
                return
            except:  # noqa: E722
                # if there is an exception for any reason, including
                # Ctrl-C during the wait() call, want to make sure
                # that the process is actually terminated
                pass

        # if we get to this point, the process is still running
        # and sigint didn't work (or we didn't try it)
        p.terminate()

    atexit.register(stop_bin)

    return p
