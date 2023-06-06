include files.mk

LDFLAGS = -pthread

obj_dir/Vtestbench:
	rm -rf obj_dir
	verilator \
		--cc \
		--exe \
		-sv \
		--trace \
		--top-module testbench \
		-I../../deps/umi/umi/rtl \
		-CFLAGS "-Wno-unknown-warning-option -I$(SBDIR)/cpp" \
		-LDFLAGS "$(LDFLAGS)" \
		config.vlt \
		$^
	make -C obj_dir -f Vtestbench.mk Vtestbench

.PHONY: clean
clean:
	rm -rf obj_dir
	rm -f *.vcd
