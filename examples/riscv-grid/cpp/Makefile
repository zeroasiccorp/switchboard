UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
	CPP_LIBS := -lboost_system -lpthread
else
	CPP_LIBS := -lboost_system -pthread -lrt
endif

client: client.cc ../../../cpp/umiverse.hpp
	g++ -I../../../cpp client.cc -o client $(CPP_LIBS)

.PHONY: clean
clean:
	rm -f client