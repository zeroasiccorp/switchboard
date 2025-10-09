from siliconcompiler import Design

from switchboard import sb_path


class SwitchboardDPI(Design):
    def __init__(self):
        super().__init__("switchboard_dpi")

        self.set_dataroot('localroot', sb_path() / "dpi")

        with self.active_fileset('sim'):
            self.add_file("switchboard_dpi.cc")
