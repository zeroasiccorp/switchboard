# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

def setup(chip):
    tool = 'morty'

    chip.set('tool', tool, 'exe', 'morty')
    chip.set('tool', tool, 'vendor', tool)

    chip.set('tool', tool, 'vswitch', '--version')


def parse_version(stdout):
    return stdout.split()[-1]
