TOPDIR=../..
include $(TOPDIR)/Rules.mk

OBJS += pcie-ping.o
TARGETS += pcie-ping

all: $(TARGETS)

pcie-ping: $(OBJS)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $< -o $@ $(LDFLAGS) $(LDLIBS)

-include $(OBJS:.o=.d)
CPPFLAGS += -MMD

.PHONY: clean
clean:
	rm -f $(TARGETS) $(OBJS) $(OBJS:.o=.d)
	rm -f queue-*
