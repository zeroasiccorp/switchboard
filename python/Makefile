UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	OTHER_FLAGS := -undefined dynamic_lookup
else
	OTHER_FLAGS := -fPIC
endif

CPP_LIBS := -pthread
CXXFLAGS := -O3 -Wall -shared -std=c++11
INCLUDES := $(shell python3 -m pybind11 --includes) -I../cpp

switchboard_pybind$(shell python3-config --extension-suffix): \
	switchboard_pybind.cc \
	../cpp/switchboard.hpp

	c++ $(CXXFLAGS) $(OTHER_FLAGS) $(INCLUDES) $< -o $@ $(CPP_LIBS)

.PHONY: clean
clean:
	rm -f switchboard_pybind$(shell python3-config --extension-suffix)
