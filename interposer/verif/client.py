import zmq

def run(socket):
    # assert reset
    data_as_bytes = (0).to_bytes(4, 'little')
    addr_as_bytes = (0x20000000).to_bytes(4, 'little')
    all_as_bytes = data_as_bytes + addr_as_bytes
    socket.send(all_as_bytes)
    socket.recv()

    # write program
    addr = 0
    with open('build/sw/hello.bin', 'rb') as f:
        data = f.read()
    padlen = ((len(data)+3)//4)*4
    data = data + bytes([0]*(padlen-len(data)))
    for addr in range(0, len(data), 4):
        instr_as_bytes = data[addr:addr+4]
        addr_as_bytes = addr.to_bytes(4, 'little')
        all_as_bytes = instr_as_bytes + addr_as_bytes
        socket.send(all_as_bytes)
        socket.recv()

    # release reset
    data_as_bytes = (1).to_bytes(4, 'little')
    addr_as_bytes = (0x20000000).to_bytes(4, 'little')
    all_as_bytes = data_as_bytes + addr_as_bytes
    socket.send(all_as_bytes)
    socket.recv()

    # handle output
    while True:
        # handshake
        all_as_bytes = socket.recv(8)
        socket.send(bytes([]))

        # process address
        addr = int.from_bytes(all_as_bytes[4:], 'little')
        if addr == 0x10000000:
            print(chr(all_as_bytes[0]), end='')
        elif addr == 0x10000008:
            kind = int.from_bytes(all_as_bytes[:2], 'little')
            if kind == 0x3333:
                exit_code = int.from_bytes(all_as_bytes[2:4], 'little')
                break
            if kind == 0x5555:
                exit_code = 0
                break
        
    if exit_code == 0:
        print('ALL TESTS PASSED.')
    else:
        print('ERROR!')

    # assert reset
    data_as_bytes = (0).to_bytes(4, 'little')
    addr_as_bytes = (0x20000000).to_bytes(4, 'little')
    all_as_bytes = data_as_bytes + addr_as_bytes
    socket.send(all_as_bytes)
    socket.recv()

    return exit_code

def main():
    print("Connecting to server... ", end='')
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.connect("tcp://localhost:5555")
    print("done.")

    exit_code = run(socket)
    print(f'EXIT_CODE: {exit_code}')

if __name__ == '__main__':
    main()
