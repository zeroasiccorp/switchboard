include files.d

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	CPP_LIBS := -lboost_system -lpthread
else
	CPP_LIBS := -lboost_system -pthread -lrt
endif

obj_dir/Vtestbench:
	rm -rf obj_dir
	verilator \
		--cc \
		--exe \
		-sv \
		--top-module testbench \
		-I../../../verilog/sim \
		-CFLAGS "-Wno-unknown-warning-option -I../../../../cpp" \
		-LDFLAGS "$(CPP_LIBS)" \
		config.vlt \
		$^
	make -C obj_dir -f Vtestbench.mk Vtestbench

.PHONY: clean
clean:
	rm -rf obj_dir
