from siliconcompiler import Flowgraph
from siliconcompiler.tools.surelog.parse import ElaborateTask

from switchboard.sc.sed.sed_remove import SedRemove
from switchboard.sc.morty.uniquify import UniquifyVerilogModules


class StandaloneNetlistFlow(Flowgraph):
    def __init__(self, name: str = None):
        if name is None:
            name = "standalone-netlist-flow"
        super().__init__(name)

        self.node("parse", ElaborateTask)
        self.node("remove", SedRemove)
        self.node("uniquify", UniquifyVerilogModules)

        self.edge("parse", "remove")
        self.edge("remove", "uniquify")


##################################################
if __name__ == "__main__":
    flow = StandaloneNetlistFlow()
    flow.write_flowgraph(f"{flow.name}.png")
