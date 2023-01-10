from _switchboard import PyUmiPacket, PyUmi

class UMI:
    def __init__(self):
        self.umi = PyUmi()

    def init(self, tx_uri="", rx_uri=""):
        self.umi.init(tx_uri, rx_uri)

    def write(self, p : PyUmiPacket):
        self.umi.write(p)

    def read(self, p : PyUmiPacket, srcrow=0, srccol=1):
        # default srcrow/srccol are set such that OOB reads work by default
        # revisit with a future ebrick_2d revision
        self.umi.read(p, srcrow, srccol)
