UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	CPP_LIBS := -lboost_system -lpthread
else
	CPP_LIBS := -lboost_system -pthread -lrt
endif

MODE ?= queue

%.out: %.cc ../cpp/switchboard.hpp ../cpp/umilib.hpp
	g++ -I../cpp $< -o $@ $(CPP_LIBS)

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
