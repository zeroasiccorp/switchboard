/*
 * This is a small example showing howto connect an RTL AXI Device
 * to a SystemC/TLM simulation using the TLM-2-AXI bridges.
 *
 * Copyright (c) 2022 Zero ASIC
 * Written by Edgar E. Iglesias
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include <sstream>

#define SC_INCLUDE_DYNAMIC_PROCESSES

#include "systemc"
using namespace sc_core;
using namespace sc_dt;
using namespace std;

#include "tlm.h"
#include "tlm_utils/simple_initiator_socket.h"
#include "tlm_utils/simple_target_socket.h"

#include "tlm-bridges/axi2tlm-bridge.h"
#include "tlm-bridges/tlm2axilite-bridge.h"
#include "tlm-bridges/tlm2native-bridge.h"

#include "checkers/pc-axi.h"
#include "checkers/pc-axilite.h"
#include "test-modules/signals-axi.h"
#include "test-modules/signals-axilite.h"
#include "trace/trace.h"
#include "traffic-generators/tg-tlm.h"
#include "traffic-generators/traffic-desc.h"
// clang-format off: utils.h relies on a header included by tg-tlm.h
#include "test-modules/utils.h"
// clang-format on

#include "soc/interconnect/iconnect.h"

#include "switchboard_tlm.hpp"

#include "Vloopback.h"
#include <verilated_vcd_sc.h>

using namespace utils;

#define AXI_SIG_LAYOUT 64, 512, 16, 8, 1, 19, 19
#define AXIL_SIG_LAYOUT 32, 32

SC_MODULE(Top) {
    sc_clock clk;
    sc_signal<bool> rst;   // Active high.
    sc_signal<bool> rst_n; // Active low.

    AXISignals<AXI_SIG_LAYOUT> signals_pcim;
    axi2tlm_bridge<AXI_SIG_LAYOUT> bridge_pcim;
    AXIProtocolChecker<AXI_SIG_LAYOUT> checker_pcim;
    tlm2native_bridge bridge_dma;

    AXILiteSignals<AXIL_SIG_LAYOUT> signals_ocl;
    tlm2axilite_bridge<AXIL_SIG_LAYOUT> bridge_ocl;
    AXILiteProtocolChecker<AXIL_SIG_LAYOUT> checker_ocl;

    iconnect<2, 1> queue_ic;

    SBTX_tlm tx;
    SBRX_tlm rx;

    Vloopback dut;

    void pull_rst(void) {
        rst.write(0);
        wait(400, SC_NS);
        rst.write(1);
        wait(400, SC_NS);
        rst.write(0);

        wait(400, SC_NS);
        tx.init("queue-tx");
        rx.init("queue-rx");

        // test user regs
        tx.dev_write32(0x8, 0x1);
        tx.dev_write32(0x40, 0x2);

        assert(tx.dev_read32(0x8) == 0x1);
        assert(tx.dev_read32(0x40) == 0x2);
    }

    void gen_rst_n(void) {
        rst_n.write(!rst.read());
    }

    SC_HAS_PROCESS(Top);

    Top(sc_module_name name)
        : clk("clk", sc_time(1, SC_US)), rst_n("rst_n"), signals_pcim("signals-pcim"),
          bridge_pcim("bridge-pcim"), checker_pcim("checker-pcim", AXIPCConfig::all_enabled()),
          bridge_dma("bridge_dma"), signals_ocl("signals-ocl"), bridge_ocl("bridge-ocl"),
          checker_ocl("checker-ocl", AXILitePCConfig::all_enabled()), queue_ic("queue-ic"), tx(0),
          rx(1), dut("dut") {
        SC_THREAD(pull_rst);

        SC_METHOD(gen_rst_n);
        sensitive << rst;

        // Wire up the clock and reset signals.
        bridge_pcim.clk(clk);
        bridge_pcim.resetn(rst_n);
        checker_pcim.clk(clk);
        checker_pcim.resetn(rst_n);
        bridge_ocl.clk(clk);
        bridge_ocl.resetn(rst_n);
        checker_ocl.clk(clk);
        checker_ocl.resetn(rst_n);
        dut.clk(clk);
        dut.nreset(rst_n);

        bridge_pcim.socket(bridge_dma.target_socket);

        tx.socket(*(queue_ic.t_sk[0]));
        rx.socket(*(queue_ic.t_sk[1]));
        queue_ic.memmap(0x0, 0xFFFFFFFFFFFFFFFF - 1, ADDRMODE_RELATIVE, -1, bridge_ocl.tgt_socket);

        // Wire-up the bridge and checker.
        signals_pcim.connect(bridge_pcim);
        signals_pcim.connect(checker_pcim);
        signals_ocl.connect(bridge_ocl);
        signals_ocl.connect(checker_ocl);

        // Since the AXI Dut doesn't use the same naming conventions
        // as AXISignals, we need to manually connect everything.
        dut.m_axi_awvalid(signals_pcim.awvalid);
        dut.m_axi_awready(signals_pcim.awready);
        dut.m_axi_awaddr(signals_pcim.awaddr);
        dut.m_axi_awuser(signals_pcim.awuser);
        dut.m_axi_awsize(signals_pcim.awsize);
        dut.m_axi_awlen(signals_pcim.awlen);
        dut.m_axi_awid(signals_pcim.awid);

        dut.m_axi_arvalid(signals_pcim.arvalid);
        dut.m_axi_arready(signals_pcim.arready);
        dut.m_axi_araddr(signals_pcim.araddr);
        dut.m_axi_aruser(signals_pcim.aruser);
        dut.m_axi_arsize(signals_pcim.arsize);
        dut.m_axi_arlen(signals_pcim.arlen);
        dut.m_axi_arid(signals_pcim.arid);

        dut.m_axi_wvalid(signals_pcim.wvalid);
        dut.m_axi_wready(signals_pcim.wready);
        dut.m_axi_wdata(signals_pcim.wdata);
        dut.m_axi_wstrb(signals_pcim.wstrb);
        dut.m_axi_wlast(signals_pcim.wlast);

        dut.m_axi_bvalid(signals_pcim.bvalid);
        dut.m_axi_bready(signals_pcim.bready);
        dut.m_axi_bresp(signals_pcim.bresp);
        dut.m_axi_bid(signals_pcim.bid);

        dut.m_axi_rvalid(signals_pcim.rvalid);
        dut.m_axi_rready(signals_pcim.rready);
        dut.m_axi_rdata(signals_pcim.rdata);
        dut.m_axi_rresp(signals_pcim.rresp);
        dut.m_axi_rid(signals_pcim.rid);
        dut.m_axi_rlast(signals_pcim.rlast);

        dut.s_axil_awvalid(signals_ocl.awvalid);
        dut.s_axil_awready(signals_ocl.awready);
        dut.s_axil_awaddr(signals_ocl.awaddr);

        dut.s_axil_wvalid(signals_ocl.wvalid);
        dut.s_axil_wready(signals_ocl.wready);
        dut.s_axil_wdata(signals_ocl.wdata);
        dut.s_axil_wstrb(signals_ocl.wstrb);

        dut.s_axil_bvalid(signals_ocl.bvalid);
        dut.s_axil_bresp(signals_ocl.bresp);
        dut.s_axil_bready(signals_ocl.bready);

        dut.s_axil_arvalid(signals_ocl.arvalid);
        dut.s_axil_arready(signals_ocl.arready);
        dut.s_axil_araddr(signals_ocl.araddr);

        dut.s_axil_rvalid(signals_ocl.rvalid);
        dut.s_axil_rdata(signals_ocl.rdata);
        dut.s_axil_rresp(signals_ocl.rresp);
        dut.s_axil_rready(signals_ocl.rready);
    }
};

int sc_main(int argc, char* argv[]) {
    Verilated::commandArgs(argc, argv);
    Top top("Top");

    sc_trace_file* trace_fp = sc_create_vcd_trace_file(argv[0]);

    trace(trace_fp, top, "top");
    top.signals_pcim.Trace(trace_fp);

    sc_start(SC_ZERO_TIME);

#if VM_TRACE
    Verilated::traceEverOn(true);
    // If verilator was invoked with --trace argument,
    // and if at run time passed the +trace argument, turn on tracing
    VerilatedVcdSc* tfp = NULL;
    const char* flag = Verilated::commandArgsPlusMatch("trace");
    if (flag && 0 == strcmp(flag, "+trace")) {
        tfp = new VerilatedVcdSc;
        top.dut.trace(tfp, 99);
        tfp->open("vlt_dump.vcd");
    }
#endif

    sc_start(100, SC_MS);

    // TODO: perform actual checking
    std::cout << "PASS" << std::endl;

    if (trace_fp) {
        sc_close_vcd_trace_file(trace_fp);
    }
#if VM_TRACE
    if (tfp) {
        tfp->close();
        tfp = NULL;
    }
#endif
    return 0;
}
