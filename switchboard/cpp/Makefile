TARGETS = umidriver router

all: $(TARGETS)

%: %.cc switchboard.hpp
	g++ -std=c++11 -I. $< -o $@ $(CPP_LIBS)

.PHONY: clean
clean:
	rm -f $(TARGETS)
