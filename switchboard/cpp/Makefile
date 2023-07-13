TARGETS = umidriver old_umidriver router old2new

all: $(TARGETS)

%: %.cc switchboard.hpp
	g++ -std=c++11 -I. $< -o $@ $(CPP_LIBS)

.PHONY: clean
clean:
	rm -f $(TARGETS)
