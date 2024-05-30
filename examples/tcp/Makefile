# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)

.PHONY: test
test:
	SB_MAX_RATE=1e3 ./test.py

.PHONY: clean
clean:
	rm -f *.q
	rm -f ram/*.q
	rm -rf ram/build
	rm -f fifos/*.q
	rm -rf fifos/build
