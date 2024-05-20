# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

def setup(chip):
    tool = 'sed'

    chip.set('tool', tool, 'exe', 'sed')
    chip.set('tool', tool, 'vendor', tool)
