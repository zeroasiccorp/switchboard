from _switchboard import PySbPacket, PySbTx, PySbRx

class SBTX:
    def __init__(self):
        self.tx = PySbTx()

    def init(self, uri):
        self.tx.init(uri)

    def send(self, p):
        return self.tx.send(p)

    def send_blocking(self, p):
        while not self.send(p):
            pass

class SBRX:
    def __init__(self):
        self.rx = PySbRx()

    def init(self, uri):
        self.rx.init(uri)

    def recv(self, p):
        return self.rx.recv(p)

    def recv_blocking(self, p):
        while not self.recv(p):
            pass
