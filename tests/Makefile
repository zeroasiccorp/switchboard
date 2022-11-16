TOPDIR=..
include $(TOPDIR)/Rules.mk

MODE ?= queue

TARGETS += hello.out
TARGETS += bandwidth.out
TARGETS += latency.out
TARGETS += torture.out

all: $(TARGETS)

-include $(OBJS:.o=.d)
-include $(TARGETS:.out=.d)
CPPFLAGS += -MMD

.PHONY: hello
hello: hello.out $(MODE)
	./test.py --test hello --mode $(MODE)

.PHONY: bandwidth
bandwidth: bandwidth.out $(MODE)
	./test.py --test bandwidth --mode $(MODE)

.PHONY: latency
latency: latency.out $(MODE)
	./test.py --test latency --mode $(MODE)

.PHONY: torture
torture: torture.out
	./$<

.PHONY: tcp
tcp:
	make -C ../cpp tcp-bridge

.PHONY: queue
queue:

# other tests
.PHONY: umistr
umistr: umistr.out
	./umistr.out

.PHONY: clean
clean:
	rm -f $(TARGETS)
	rm -f $(TARGETS:.out=.d)
