UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	CPP_LIBS := -lboost_system -lpthread
else
	CPP_LIBS := -lboost_system -pthread -lrt
endif

%: %.cc switchboard.hpp
	g++ -std=c++11 -I. $< -o $@ $(CPP_LIBS)

.PHONY: clean
clean:
	rm -f umidriver router
