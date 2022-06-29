#include "Vzverif_top.h"
#include "verilated_vcd_c.h"
#include <inttypes.h>

enum state {AXI_RST, PGM_CPU, RUN_CPU};

int main(int argc, char **argv, char **env)
{
	printf("Built with %s %s.\n", Verilated::productName(), Verilated::productVersion());
	printf("Recommended: Verilator 4.0 or later.\n");

	Verilated::commandArgs(argc, argv);
	Vzverif_top* top = new Vzverif_top;

	// Tracing (vcd)
	VerilatedVcdC* tfp = NULL;
	const char* flag_vcd = Verilated::commandArgsPlusMatch("vcd");
	if (flag_vcd && 0==strcmp(flag_vcd, "+vcd")) {
		Verilated::traceEverOn(true);
		tfp = new VerilatedVcdC;
		top->trace (tfp, 99);
		tfp->open("testbench.vcd");
	}

	// Firmware file
	FILE *firmware_fd = NULL;
	const char* flag_firmware = Verilated::commandArgsPlusMatch("firmware");
	if (flag_firmware) {
		flag_firmware += 10;
		firmware_fd = fopen(flag_firmware, "rb");
	}

	top->clk = 1;
	top->axi_rst = 1;
	int t = 0;

	uint32_t addr = 0;
	uint16_t exit_code = 0;
	bool write_in_progress = false;
	enum state cur_state = AXI_RST;

	while (!Verilated::gotFinish()) {
		// update inputs before a falling edge
		if (top->clk) {
			if (cur_state == AXI_RST) {
				// release AXI from reset

				if (t > 200) {
					top->axi_rst = 0;
					cur_state = PGM_CPU;
				}
			} else if (cur_state == PGM_CPU) {
				// program the CPU

				uint8_t buf[4];

				if (write_in_progress) {
					if (top->ext_awready) {
						top->ext_awvalid = 0;
					}
					if (top->ext_wready) {
						top->ext_wvalid = 0;
					}
					if (top->ext_bvalid) {
						top->ext_bready = 1;
						write_in_progress = false;
					}		
				} else if (fread(buf, 1, 4, firmware_fd) != 0) {
					top->ext_awaddr = addr;
					top->ext_awvalid = 1;
					top->ext_wdata = (buf[3] << 24) | (buf[2] << 16) | (buf[1] << 8) | buf[0];
					top->ext_wvalid = 1;
					top->ext_bready = 0;
					write_in_progress = true;
					addr += 4;
				} else {
					// prepare to run the CPU program by de-asserting its reset
					// and de-asserting the BREADY handshake from the last memory transaction
					top->resetn = 1;
					top->ext_bready = 0;
					cur_state = RUN_CPU;
				}
			} else {
				// look for writes
				if (top->ctrl_awvalid && top->ctrl_wvalid &&
					((!top->ctrl_awready) && (!top->ctrl_wready)) &&
					((!top->ctrl_bvalid) || top->ctrl_bready)) {
					if (top->ctrl_awaddr == 0x10000008) {
						if ((top->ctrl_wdata & 0xffff) == 0x3333) {
							exit_code = (top->ctrl_wdata >> 16) & 0xffff;
							break;
						} else if ((top->ctrl_wdata & 0xffff) == 0x5555) {
							exit_code = 0;
							break;
						}
					} else if (top->ctrl_awaddr == 0x10000000) {
						printf("%c", top->ctrl_wdata & 0xff);
					} else {
						printf("OUT-OF-BOUNDS MEMORY WRITE TO %08x\n", top->ctrl_awaddr);
						exit_code = 1;
						break;
					}

					// handshaking
					top->ctrl_awready = 1;
					top->ctrl_wready = 1;
					top->ctrl_bvalid = 1;
				} else {
					top->ctrl_awready = 0;
					top->ctrl_wready = 0;
					top->ctrl_bvalid = top->ctrl_bvalid && (!top->ctrl_bready);
				}
			}
		}

		// update the clock
		top->clk = !top->clk;

		top->eval();

		// dump waveforms
		if (tfp) tfp->dump (t);
		t += 5;
	}

	if (tfp) tfp->close();
	delete top;

	if (exit_code == 0) {
		printf("ALL TESTS PASSED.\n");
	} else {
		printf("ERROR!\n");
	}
	exit(exit_code);
}

