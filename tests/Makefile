UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	LDLIBS := -lboost_system -lpthread
else
	LDLIBS := -lboost_system -pthread -lrt
endif

MODE ?= queue

CPPFLAGS += -I../cpp

TARGETS += hello.out
TARGETS += bandwidth.out
TARGETS += latency.out

-include $(TARGETS:.out=.d)
CPPFLAGS += -MMD

%.out: %.cc
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $< -o $@ $(LDFLAGS) $(LDLIBS)

.PHONY: hello
hello: hello.out $(MODE)
	./test.py --test hello --mode $(MODE)

.PHONY: bandwidth
bandwidth: bandwidth.out $(MODE)
	./test.py --test bandwidth --mode $(MODE)

.PHONY: latency
latency: latency.out $(MODE)
	./test.py --test latency --mode $(MODE)

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
	rm -f *.out
