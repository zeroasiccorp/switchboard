from siliconcompiler import Design

from switchboard import sb_path


class Verilator(Design):
    def __init__(self):
        super().__init__("verilator")

        self.set_dataroot('localroot', sb_path() / "verilator")

        with self.active_fileset('sim'):
            self.add_file("testbench.cc")
