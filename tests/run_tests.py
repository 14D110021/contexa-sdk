#!/usr/bin/env python
"""
Test runner for Contexa SDK.

This script installs the test dependencies and runs the pytest suite with coverage reporting.
"""

import os
import sys
import subprocess


def install_dependencies():
    """Install test dependencies."""
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])


def run_tests():
    """Run the test suite with coverage reporting."""
    # Get the root directory of the project
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/", "-v",
        f"--cov={os.path.basename(root_dir)}",
        "--cov-report=term",
        "--cov-report=html"
    ]
    
    subprocess.call(cmd)


if __name__ == "__main__":
    # Install dependencies
    print("Installing test dependencies...")
    install_dependencies()
    
    # Run tests
    print("\nRunning tests...")
    run_tests()
    
    # Output report location
    print("\nCoverage report generated at htmlcov/index.html") 