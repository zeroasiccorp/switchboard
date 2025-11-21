from siliconcompiler import Design

from umi.sumi import Unpack, Pack

from switchboard import sb_path


class Common(Design):
    def __init__(self):

        super().__init__("common")

        files = [
            "uart_xactor.sv",
            "umi_gpio.v"
        ]
        deps = [Unpack(), Pack()]

        self.set_dataroot('sb_verilog_common', sb_path() / "verilog" / "common")

        with self.active_fileset('rtl'):
            self.add_idir(".")
            for item in files:
                self.add_file(item)
            for item in deps:
                self.add_depfileset(item)
