TOPDIR=../..
include $(TOPDIR)/Rules.mk

OBJS += umidriver.o
OBJS += router.o
TARGETS = umidriver router

all: $(TARGETS)

umidriver: umidriver.o
router: router.o

-include $(OBJS:.o=.d)
CPPFLAGS += -MMD

%: %.cc switchboard.hpp
	g++ -std=c++11 -I. $< -o $@ $(CPP_LIBS)

.PHONY: clean
clean:
	rm -f umidriver router
