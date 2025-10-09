from siliconcompiler import Design

from umi.sumi import Fifo, RAM

from switchboard.verilog.sim.switchboard_sim import SwitchboardSim
from switchboard import sb_path


class UmiRam(Design):

    def __init__(self):
        super().__init__("testbench")

        top_module = "testbench"

        dr_path = sb_path() / ".." / "examples" / "umiram"

        self.set_dataroot('umiram', dr_path)

        files = [
            "testbench.sv",
            "../common/verilog/umiram.sv"
        ]

        deps = [
            Fifo(),
            RAM()
        ]

        with self.active_fileset('rtl'):
            self.set_topmodule(top_module)
            self.add_depfileset(SwitchboardSim())
            for item in files:
                self.add_file(item)
            for item in deps:
                self.add_depfileset(item)

        with self.active_fileset('verilator'):
            self.set_topmodule(top_module)
            self.add_depfileset(self, "rtl")

        with self.active_fileset('icarus'):
            self.set_topmodule(top_module)
            self.add_depfileset(self, "rtl")
