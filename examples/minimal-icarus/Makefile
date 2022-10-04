.PHONY: hello
hello: prereqs
	./scripts/test.py

.PHONY: prereqs
prereqs:
	make -C cpp client
	make -C icarus

.PHONY: clean
clean:
	make -C cpp clean
	make -C icarus clean
