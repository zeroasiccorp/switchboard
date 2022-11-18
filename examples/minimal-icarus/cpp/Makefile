TOPDIR=../../..
include $(TOPDIR)/Rules.mk

OBJS += client.o
TARGETS = client

all: $(TARGETS)

-include $(OBJS:.o=.d)
CPPFLAGS += -MMD

client: $(OBJS)
	$(LINK.cc) $^ $(LDLIBS) -o $@

.PHONY: clean
clean:
	rm -f $(OBJS)
	rm -f $(TARGETS)
