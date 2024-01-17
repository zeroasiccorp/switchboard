# Utilities for working with Xyce

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)


def xyce_flags():
    import shutil
    from pathlib import Path

    xyce = shutil.which('Xyce')

    if not xyce:
        raise RuntimeError('Xyce install not found')

    xyce_prefix = Path(xyce).parent.parent

    ldflags = [
        f'-L{xyce_prefix / "lib"}',
        '-lxycecinterface'
    ]

    cincludes = [
        f'{xyce_prefix / "include"}'
    ]

    return cincludes, ldflags
