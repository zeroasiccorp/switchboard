# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from siliconcompiler import Task


class UniquifyVerilogModules(Task):

    def __init__(self):
        super().__init__()

        self.add_parameter(
            name='suffix',
            type='str',
            help='suffix to be added to the end of module names'
        )

        self.add_parameter(
            name='prefix',
            type='str',
            help='prefix to be added to the beginning of module names'
        )

    def tool(self):
        return "morty"

    def task(self):
        return "uniquify_verilog_modules"

    def setup(self):
        super().setup()

        self.set_exe("morty")

        self.add_input_file(ext="sv")
        self.add_output_file(ext="sv")

    def runtime_options(self):
        options = super().runtime_options()

        idirs = []
        for lib, fileset in self.project.get_filesets():
            idirs.extend(lib.get_idir(fileset))

        cmdlist = []

        prefix = self.get("var", "prefix")
        if prefix:
            cmdlist.extend(['--prefix', prefix])

        suffix = self.get("var", "suffix")
        if suffix:
            cmdlist.extend(['--suffix', suffix])

        out_file = f"outputs/{self.design_topmodule}.sv"

        cmdlist.extend(['-o', out_file])

        for value in idirs:
            cmdlist.append('-I' + value)

        input_file = f"inputs/{self.design_topmodule}.sv"

        options.extend(cmdlist)
        options.append(input_file)

        return options
