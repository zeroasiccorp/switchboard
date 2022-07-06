.PHONY: iverilog
iverilog: zmq_vpi.o testbench_vpi.vvp
	vvp -n -M. -mzmq_vpi testbench_vpi.vvp

zmq_vpi.o: zmq_vpi.c
	iverilog-vpi zmq_vpi.c -lzmq

testbench_vpi.vvp: testbench_vpi.v
	iverilog -o testbench_vpi.vvp -s testbench_vpi -f files.txt

.PHONY: clean
clean:
	rm -f *.vvp *.vpi *.vcd