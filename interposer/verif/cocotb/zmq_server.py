import zmq
import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def run(dut):
    """Run server for ZMQ"""

    CONTEXT = zmq.Context()
    socket = CONTEXT.socket(zmq.PAIR)
    socket.bind("tcp://*:5555")

    rx_in_progress = False
    tx_in_progress = False
    clk = 0
    umi_packet_rx = 0
    umi_valid_rx = 0
    umi_ready_tx = 0

    dut.clk.value = clk
    dut.umi_packet_rx.value = umi_packet_rx
    dut.umi_valid_rx.value = umi_valid_rx
    dut.umi_ready_tx.value = umi_ready_tx

    await Timer(5, units="ns")

    while True:
        # determine next value of outputs when clock is about
        # to go high (i.e., when it currently reads low).  these
        # outputs are driven right after the clock edge
        if not clk:
            # write data to the device
            if rx_in_progress:
                if dut.umi_ready_rx.value:
                    umi_valid_rx = 0
                    rx_in_progress = False
            else:
                try:
                    rbuf = socket.recv(flags=zmq.NOBLOCK)
                except:
                    rbuf = bytes([])
                if (len(rbuf) == 32):
                    socket.send(bytes([]))
                    umi_packet_rx = int.from_bytes(rbuf, 'little')
                    umi_valid_rx = 1
                    rx_in_progress = True

            # look for writes
            if tx_in_progress:
                umi_ready_tx = 0
                tx_in_progress = False
            else:
                if dut.umi_valid_tx.value:
                    packet = int(dut.umi_packet_tx.value).to_bytes(32, 'little')
                    socket.send(packet)
                    socket.recv()
                    umi_ready_tx = 1
                    tx_in_progress = True

        # generate clock edge
        clk = not clk
        dut.clk.value = clk
    
        # drive new outputs
        if clk:
            await Timer(1, units="ns")
            dut.umi_packet_rx.value = umi_packet_rx
            dut.umi_valid_rx.value = umi_valid_rx
            dut.umi_ready_tx.value = umi_ready_tx
            await Timer(4, units="ns")
        else:
            await Timer(5, units="ns")
