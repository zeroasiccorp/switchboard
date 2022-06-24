#!/usr/bin/env python3
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.

from pathlib import Path

def makehex(input, output=None, nwords=32768):
    # determine output file if needed
    if output is None:
        output = Path(input).with_suffix('.hex')

    # read input file
    with open(input, "rb") as f:
        bindata = f.read()

    # pad to a fixed length
    assert len(bindata) <= 4*nwords
    bindata += bytes([0]*((4*nwords)-len(bindata)))

    # print words
    # TODO: handle 32 and 64 bit
    with open(output, 'w') as f:
        for i in range(nwords):
            w = bindata[4*i : 4*i+4]
            f.write('%02x%02x%02x%02x\n' % (w[3], w[2], w[1], w[0]))
