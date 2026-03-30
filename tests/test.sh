#!/bin/bash

python3 tests/test_logic.py

if [ $? -eq 0 ]; then
    echo "Benchmark Passed: AI successfully cleaned the data."
    exit 0
else
    echo "Benchmark Failed: AI logic is incorrect."
    exit 1
fi
