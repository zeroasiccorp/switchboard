from siliconcompiler import Design

from switchboard.verilator.verilator import Verilator
from switchboard.dpi.switchboard_dpi import SwitchboardDPI
from switchboard.verilog.common.common import Common
from switchboard import sb_path


class SwitchboardSim(Design):
    def __init__(self):
        super().__init__("sb_sim")

        files = [
            "auto_stop_sim.sv",
            "perf_meas_sim.sv",
            "queue_to_sb_sim.sv",
            "queue_to_umi_sim.sv",
            "sb_axil_m.sv",
            "sb_axi_m.sv",
            "sb_jtag_rbb_sim.sv",
            "sb_to_queue_sim.sv",
            "umi_to_queue_sim.sv",
            "sb_axil_s.sv",
            "sb_clk_gen.sv",
            "sb_rx_sim.sv",
            "sb_tx_sim.sv",
            "umi_rx_sim.sv",
            "umi_tx_sim.sv",
            "xyce_intf.sv",
            "sb_apb_m.sv"
        ]
        deps = [Common()]

        self.set_dataroot("sb_verilog_sim", sb_path() / "verilog" / "sim")

        with self.active_fileset("rtl"):
            for item in files:
                self.add_file(item)
            for item in deps:
                self.add_depfileset(item)

        with self.active_fileset("verilator"):
            self.add_depfileset(self, "rtl")
            self.add_depfileset(Verilator())
            self.add_depfileset(SwitchboardDPI())

        with self.active_fileset("icarus"):
            self.add_depfileset(self, "rtl")
            self.add_define("__ICARUS__")
