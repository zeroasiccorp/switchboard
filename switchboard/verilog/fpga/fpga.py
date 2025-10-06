from siliconcompiler import Design

from switchboard import path as sb_path


class FPGA(Design):
    def __init__(self):
        files = [
            "axi_reader.sv"
        ]
        deps = []

        self.set_dataroot('sb_verilog_fpga', sb_path() / "verilog" / "fpga")

        with self.active_fileset('rtl'):
            for item in files:
                self.add_files(item)
            for item in deps:
                self.add_depfileset(item)
