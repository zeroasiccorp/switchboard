SBDIR := $(shell switchboard --path)

.PHONY: python
python:
	./test.py

.PHONY: clean
clean:
	rm -rf build obj_dir
	rm -f queue-* *.q
	rm -f *.vcd *.fst *.fst.hier
