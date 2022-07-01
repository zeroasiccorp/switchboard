import zmq
import cocotb
from cocotb.triggers import Timer

from zverif.umi import UmiPacket

@cocotb.test()
async def run(dut):
    """Run server for ZMQ"""

    CONTEXT = zmq.Context()
    socket = CONTEXT.socket(zmq.PAIR)
    socket.bind("tcp://*:5555")

    write_in_progress = False
    clk = 0
    ext_awvalid = 0
    ext_wvalid = 0
    ext_bready = 0
    ext_awaddr = 0
    ext_wdata = 0
    ctrl_awready = 0
    ctrl_wready = 0
    ctrl_bvalid = 0

    dut.clk.value = clk
    dut.ext_awaddr.value = ext_awaddr
    dut.ext_awvalid.value = ext_awvalid
    dut.ext_wdata.value = ext_wdata
    dut.ext_wvalid.value = ext_wvalid
    dut.ext_bready.value = ext_bready
    dut.ctrl_awready.value = ctrl_awready
    dut.ctrl_wready.value = ctrl_wready
    dut.ctrl_bvalid.value = ctrl_bvalid

    await Timer(5, units="ns")

    while True:
        # determine next value of outputs when clock is about
        # to go high (i.e., when it currently reads low).  these
        # outputs are driven right after the clock edge
        if not clk:
            # write data to the device
            if write_in_progress:
                if dut.ext_awready.value:
                    ext_awvalid = 0
                if dut.ext_wready.value:
                    ext_wvalid = 0
                if dut.ext_bvalid.value:
                    ext_bready = 1
                    write_in_progress = False
            else:
                ext_bready = 0
                try:
                    rbuf = socket.recv(flags=zmq.NOBLOCK)
                except:
                    rbuf = bytes([])
                if (len(rbuf) == 32):
                    socket.send(bytes([]))
                    packet = UmiPacket.unpack(rbuf)
                    ext_awaddr = packet.dstaddr & 0xffffffff
                    ext_wdata = packet.data & 0xffffffff
                    #print(f"RECV {ext_wdata} @ {ext_awaddr}")
                    ext_awvalid = 1
                    ext_wvalid = 1
                    write_in_progress = True

            # look for writes
            if (dut.ctrl_awvalid.value and dut.ctrl_wvalid.value and
                ((not dut.ctrl_awready.value) and (not dut.ctrl_wready.value)) and
                ((not dut.ctrl_bvalid.value) or dut.ctrl_bready.value)):
                #print(f"SEND {dut.ctrl_wdata.value} @ {dut.ctrl_awaddr.value}")
                packet = UmiPacket(
                    dstaddr=int(dut.ctrl_awaddr.value),
                    data=int(dut.ctrl_wdata.value)
                )
                socket.send(packet.pack())
                socket.recv()

                # handshaking
                ctrl_awready = 1
                ctrl_wready = 1
                ctrl_bvalid = 1
            else:
                ctrl_awready = 0
                ctrl_wready = 0
                ctrl_bvalid = dut.ctrl_bvalid.value and (not dut.ctrl_bready.value)

        # generate clock edge
        clk = not clk
        dut.clk.value = clk
    
        # drive new outputs
        if clk:
            await Timer(1, units="ns")
            dut.ext_awvalid.value = ext_awvalid
            dut.ext_wvalid.value = ext_wvalid
            dut.ext_bready.value = ext_bready
            dut.ext_awaddr.value = ext_awaddr
            dut.ext_wdata.value = ext_wdata
            dut.ctrl_awready.value = ctrl_awready
            dut.ctrl_wready.value = ctrl_wready
            dut.ctrl_bvalid.value = ctrl_bvalid
            await Timer(4, units="ns")
        else:
            await Timer(5, units="ns")
