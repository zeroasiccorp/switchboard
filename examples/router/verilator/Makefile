include files.mk

LDFLAGS = -pthread

obj_dir/Vtestbench:
	rm -rf obj_dir
	verilator \
		--cc \
		--exe \
		-sv \
		--top-module testbench \
		-CFLAGS "-Wno-unknown-warning-option -I$(SBDIR)/cpp" \
		-LDFLAGS "$(LDFLAGS)" \
		$^
	make -C obj_dir -f Vtestbench.mk Vtestbench

.PHONY: clean
clean:
	rm -rf obj_dir
