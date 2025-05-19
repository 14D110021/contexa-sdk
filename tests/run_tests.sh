#!/bin/bash

# Install test dependencies
pip install -r tests/requirements.txt

# Run tests with coverage
python -m pytest tests/ -v --cov=contexa_sdk --cov-report=term --cov-report=html

# Output the coverage report location
echo "Coverage report generated at htmlcov/index.html" 