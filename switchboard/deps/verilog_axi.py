from siliconcompiler import Design


class VerilogAxi(Design):
    def __init__(self):

        self.set_dataroot(
            name="verilog_axi",
            path="git+https://github.com/alexforencich/verilog-axis.git@master",
            tag="25912d48fec2abbf3565bbefe402c1cff99fe470"
        )

        path = "rtl"

        files = [
            f"{path}/arbiter.v",
        ]

        with self.active_fileset('rtl'):
            for item in files:
                self.add_files(item)

