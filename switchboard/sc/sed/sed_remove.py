# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

from siliconcompiler import Task


class SedRemove(Task):

    def __init__(self):
        super().__init__()

        self.add_parameter(
            name="to_remove",
            type="[str]",
            help="strings to remove from the Verilog source file"
        )

    def tool(self):
        return "sed"

    def task(self):
        return "remove"

    def setup(self):
        super().setup()

        self.set_exe("sed")

        self.add_output_file(ext="sv")

    def runtime_options(self):
        options = super().runtime_options()

        to_remove = self.get("var", "to_remove")

        print(f"to remove = {to_remove}")

        script = [f's/{elem}//g' for elem in to_remove]
        script += [f'w outputs/{self.design_topmodule}.sv']
        print(f"script = {script}")
        script = '; '.join(script)

        options.extend(["-n", f'{script}', ])

        #######################
        # Sources
        #######################
        filesets = self.project.get_filesets()
        for lib, fileset in filesets:
            for value in lib.get_file(fileset=fileset, filetype="systemverilog"):
                options.append(value)
        for lib, fileset in filesets:
            for value in lib.get_file(fileset=fileset, filetype="verilog"):
                options.append(value)

        return options
