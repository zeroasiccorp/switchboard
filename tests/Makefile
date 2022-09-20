UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	CPP_LIBS := -lboost_system -lpthread
else
	CPP_LIBS := -lboost_system -pthread -lrt
endif

%: %.cc ../cpp/switchboard.hpp
	g++ -I../cpp $< -o $@ $(CPP_LIBS)

.PHONY: clean
clean:
	rm -f umistr