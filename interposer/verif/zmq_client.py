import sys
import zmq

def run(dut, program):
    # assert reset
    dut.send(0, 0x20000000)

    # write program
    with open(program, 'rb') as f:
        data = f.read()
    for addr in range(0, len(data), 4):
        elem = data[addr:addr+4]  # get 4-byte chunk
        elem = elem + bytes([0]*(4-len(elem)))  # pad if needed
        dut.send(elem, addr)

    # release reset
    dut.send(1, 0x20000000)

    # handle output
    while True:
        data, addr = dut.recv()

        # process address
        if addr == 0x10000000:
            print(chr(data & 0xff), end='', flush=True)
        elif addr == 0x10000008:
            kind = data & 0xffff
            if kind == 0x3333:
                exit_code = (data >> 16) & 0xffff
                break
            if kind == 0x5555:
                exit_code = 0
                break
        
    if exit_code == 0:
        print('ALL TESTS PASSED.')
    else:
        print('ERROR!')

    # assert reset
    dut.send(0, 0x20000000)

    return exit_code

class DUT:
    CONTEXT = zmq.Context()  # context is shared across DUT instances
    def __init__(self, uri):
        print("Connecting to server... ", end='')
        self.socket = self.CONTEXT.socket(zmq.PAIR)
        self.socket.connect(uri)
        print("done.")
    
    def send(self, data, addr):
        # convert data and address to bytes as needed
        if isinstance(data, int):
            data = data.to_bytes(4, 'little')
        if isinstance(addr, int):
            addr = addr.to_bytes(4, 'little')

        # make sure data and addr are the right size
        assert len(data) == 4, 'data must be 4 bytes'
        assert len(addr) == 4, 'addr must be 4 bytes'

        # concatenate data and addr
        transaction = data + addr

        # send message
        self.socket.send(transaction)
        self.socket.recv()
    
    def recv(self, as_ints=True):
        # receive data
        transaction = self.socket.recv(8)
        self.socket.send(bytes([]))

        # split into data and address
        data, addr = transaction[:4], transaction[4:]

        # convert to integers if desired
        if as_ints:
            data = int.from_bytes(data, 'little')
            addr = int.from_bytes(addr, 'little')
        
        return data, addr

def main():
    dut = DUT("tcp://localhost:5555")
    exit_code = run(dut, 'build/sw/hello.bin')
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
