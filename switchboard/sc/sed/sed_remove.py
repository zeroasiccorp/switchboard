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

        self.add_input_file(ext="sv")
        self.add_output_file(ext="sv")

    def runtime_options(self):
        options = super().runtime_options()

        to_remove = self.get("var", "to_remove")

        script = [f's/{elem}//g' for elem in to_remove]
        script += [f'w outputs/{self.design_topmodule}.sv']
        script = '; '.join(script)

        options.extend(["-n", f'{script}', ])

        input_file = f"inputs/{self.design_topmodule}.sv"

        options.append(input_file)

        return options
