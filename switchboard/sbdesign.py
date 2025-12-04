from siliconcompiler import Design
from typing import List, Tuple


class SbDesign(Design):
    def __init__(
            self,
            name: str = "SbDesign",
            trace: bool = False,
            topmodule: str = None,
            dep: List[Design] = None,
            files: List[str] = None,
            idir: List[str] = None,
            define: List[str] = None,
            undefine: List[str] = None,
            param: List[Tuple] = None
    ):

        super().__init__(name)

        # Taking care of Nones
        if idir is None:
            idir = []
        if dep is None:
            dep = []
        if define is None:
            define = []
        if undefine is None:
            undefine = []
        if param is None:
            param = []

        # Setting RTL list, others outside
        with self.active_fileset('rtl'):
            if topmodule:
                self.set_topmodule(topmodule)
            for item in files:
                self.add_file(item)
            for item in idir:
                self.add_idir(item)
            for item in dep:
                self.add_depfileset(item)
            for item in define:
                self.add_define(item)
            for item in undefine:
                self.add_undefine(item)
            for item in param:
                self.add_param(item[0], item[1])

        with self.active_fileset('icarus'):
            if topmodule:
                self.set_topmodule(topmodule)
            self.add_depfileset(self, 'rtl')
            if trace:
                self.add_define("SB_TRACE")
