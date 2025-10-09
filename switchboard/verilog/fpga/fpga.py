from siliconcompiler import Design

from switchboard import sb_path


class FPGA(Design):
    def __init__(self):
        super().__init__("FPGA")

        files = [
            "axi_reader.sv"
        ]
        deps = []

        self.set_dataroot('sb_verilog_fpga', sb_path() / "verilog" / "fpga")

        with self.active_fileset('rtl'):
            for item in files:
                self.add_file(item)
            for item in deps:
                self.add_depfileset(item)
