# Utilities for working with Verilator
# Copyright (C) 2023 Zero ASIC

# TODO: replace with SiliconCompiler functionality

import atexit
import signal
import subprocess


def verilator_run(bin, plusargs=None, stop_timeout=10):
    cmd = []

    cmd += [bin]

    if plusargs is not None:
        assert isinstance(plusargs, list), 'plusargs must be a list'
        for plusarg in plusargs:
            if isinstance(plusarg, (list, tuple)):
                assert len(plusarg) == 2, 'only lists/tuples of length 2 allowed'
                cmd += [f'+{plusarg[0]}+{plusarg[1]}']
            else:
                cmd += [f'+{plusarg}']

    cmd = [str(elem) for elem in cmd]
    print(' '.join(cmd))

    p = subprocess.Popen(cmd)

    def stop_sim(p=p, stop_timeout=stop_timeout):
        try:
            p.send_signal(signal.SIGINT)
            p.wait(stop_timeout)
        except:  # noqa: E722
            # if there is an exception for any reason, including
            # Ctrl-C during the wait() call, terminate the process
            # to make sure it isn't hanging around after switchboard
            # exits
            p.terminate()

    atexit.register(stop_sim)
