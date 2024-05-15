#!/bin/bash

# Loop through subdirectories, running 'make clean'

for dir in */; do
    # Run 'make clean' if a Makefile exists

    if [ -f "${dir}Makefile" ]; then
        echo "Running 'make clean' in $dir"
        (cd "$dir" && make clean)
    fi
done
