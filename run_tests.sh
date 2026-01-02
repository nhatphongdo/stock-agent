#!/bin/bash

# Activate virtual environment if it exists, otherwise assume python3 is correct or use venv/bin/python directly
if [ -d "venv" ]; then
    PYTHON_CMD="./venv/bin/python"
else
    PYTHON_CMD="python3"
fi

echo "Running all tests in 'tests' folder..."
TEST_TICKER="VNM" $PYTHON_CMD -m unittest discover -s tests -p "test_*.py"
