# test_my_design.py (extended)

import cocotb
from cocotb.triggers import Timer
from cocotb.triggers import FallingEdge

import zmq
CONTEXT = zmq.Context()

@cocotb.test()
async def run(dut):
    """Run server for ZMQ"""

    socket = CONTEXT.socket(zmq.PAIR)
    socket.bind("tcp://*:5555")

    dut.clk.value = 0
    dut.ext_awaddr.value = 0
    dut.ext_awvalid.value = 0
    dut.ext_wdata.value = 0
    dut.ext_wvalid.value = 0
    dut.ext_bready.value = 0

    dut.ctrl_awready.value = 0
    dut.ctrl_wready.value = 0 
    dut.ctrl_bvalid.value = 0

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
                if (len(rbuf) == 8):
                    socket.send(bytes([]))
                    ext_awaddr = (rbuf[7] << 24) | (rbuf[6] << 16) | (rbuf[5] << 8) | rbuf[4]
                    ext_wdata = (rbuf[3] << 24) | (rbuf[2] << 16) | (rbuf[1] << 8) | rbuf[0]
                    #print(f"RECV {ext_wdata} @ {ext_awaddr}")
                    ext_awvalid = 1
                    ext_wvalid = 1
                    write_in_progress = True

            # look for writes
            if (dut.ctrl_awvalid.value and dut.ctrl_wvalid.value and
                ((not dut.ctrl_awready.value) and (not dut.ctrl_wready.value)) and
                ((not dut.ctrl_bvalid.value) or dut.ctrl_bready.value)):
                #print(f"SEND {dut.ctrl_wdata.value} @ {dut.ctrl_awaddr.value}")
                sbuf = [0]*8
                sbuf[7] = (dut.ctrl_awaddr.value >> 24) & 0xff
                sbuf[6] = (dut.ctrl_awaddr.value >> 16) & 0xff
                sbuf[5] = (dut.ctrl_awaddr.value >> 8) & 0xff
                sbuf[4] = (dut.ctrl_awaddr.value >> 0) & 0xff
                sbuf[3] = (dut.ctrl_wdata.value >> 24) & 0xff
                sbuf[2] = (dut.ctrl_wdata.value >> 16) & 0xff
                sbuf[1] = (dut.ctrl_wdata.value >> 8) & 0xff
                sbuf[0] = (dut.ctrl_wdata.value >> 0) & 0xff
                socket.send(bytes(sbuf))
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
