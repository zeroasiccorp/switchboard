TOPDIR=../../..
include $(TOPDIR)/Rules.mk

OBJS += driver.o
TARGETS = driver

all: $(TARGETS)

-include $(OBJS:.o=.d)
CPPFLAGS += -MMD

client: $(OBJS)
	$(LINK.cc) $^ $(LDLIBS) -o $@

.PHONY: clean
clean:
	rm -f $(OBJS)
	rm -f $(TARGETS)
