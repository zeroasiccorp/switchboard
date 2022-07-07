# verilator_dpi

.PHONY: verilator_dpi
verilator_dpi: verilator_dpi/Vtestbench
	./verilator_dpi/Vtestbench

verilator_dpi/Vtestbench:
	rm -rf verilator_dpi
	verilator \
		--cc \
		--exe \
		--build \
		-sv \
		-Mdir verilator_dpi \
		--top testbench \
		-DDPI \
		-DCYCLES_PER_RECV=1000 \
		-DCYCLES_PER_MEAS=10000000 \
		-CFLAGS "-Wno-unknown-warning-option" \
		-LDFLAGS "-lzmq" \
		testbench.cc \
		zmq_dpi.cc \
		../verilator/config.vlt \
		-f files.txt

.PHONY: iverilog_vpi
iverilog_vpi: iverilog_vpi/zmq_vpi.o iverilog_vpi/testbench.vvp
	vvp -n -M iverilog_vpi -m zmq_vpi iverilog_vpi/testbench.vvp

iverilog_vpi/zmq_vpi.o: zmq_vpi.c
	iverilog-vpi zmq_vpi.c -lzmq
	mkdir -p iverilog_vpi
	mv zmq_vpi.vpi iverilog_vpi/.
	mv zmq_vpi.o iverilog_vpi/.

iverilog_vpi/testbench.vvp: testbench.sv
	mkdir -p iverilog_vpi
	iverilog \
		-s testbench \
		-DCYCLES_PER_RECV=10 \
		-DCYCLES_PER_MEAS=20000 \
		-o iverilog_vpi/testbench.vvp \
		-f files.txt

.PHONY: clean
clean:
	rm -rf iverilog_vpi
	rm -rf verilator_dpi
	rm -f *.vcd