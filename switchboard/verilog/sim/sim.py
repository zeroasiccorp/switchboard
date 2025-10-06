from siliconcompiler import Design

from switchboard import sb_path


class Sim(Design):
    def __init__(self):
        super().__init__("sb_sim")

        files = [
            "sb_clk_gen.sv",
            "queue_to_sb_sim.sv",
            "sb_to_queue_sim.sv",
            "umi_to_queue_sim.sv",
            "queue_to_umi_sim.sv",
            "umi_rx_sim.sv"
        ]
        deps = []

        self.set_dataroot('sb_verilog_sim', sb_path() / "verilog" / "sim")

        with self.active_fileset('rtl'):
            for item in files:
                self.add_file(item)
            for item in deps:
                self.add_depfileset(item)
