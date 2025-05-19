# Contributing to Contexa SDK

Thank you for your interest in contributing to Contexa SDK! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

This project adheres to a Code of Conduct that establishes how we collaborate. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git

### Setting Up the Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/contexa_sdk.git
   cd contexa_sdk
   ```
3. Install the package in development mode with all dependencies:
   ```bash
   pip install -e ".[all,dev]"
   ```
4. Create a branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Process

1. Check the issues list for open tasks or create a new issue for your proposed feature
2. Assign the issue to yourself to let others know you're working on it
3. Implement your changes following our coding standards
4. Write tests for your changes
5. Run the test suite to ensure everything passes
6. Update documentation as needed
7. Create a pull request with your changes

## Pull Request Process

1. Update the README.md or relevant documentation with details of changes
2. Run tests to verify your changes don't break existing functionality
3. Ensure your code follows the project's coding standards
4. Submit your pull request with a clear description of the changes
5. Address any feedback from code reviews
6. Once approved, your PR will be merged by a maintainer

## Coding Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use type hints for all function parameters and return values
- Document your code using Google-style docstrings
- Keep lines under 100 characters
- Use meaningful variable and function names
- Write modular, reusable code
- Follow the project's architecture and design patterns

### Code Formatting

We use the following tools for code formatting and linting:

- [Black](https://black.readthedocs.io/) for code formatting
- [Flake8](https://flake8.pycqa.org/) for linting
- [isort](https://pycqa.github.io/isort/) for sorting imports

Run these before submitting a PR:

```bash
black contexa_sdk tests
flake8 contexa_sdk tests
isort contexa_sdk tests
```

## Testing Guidelines

- All new features should have corresponding tests
- All bugfixes should include a test that verifies the bug is fixed
- Tests should be placed in the `tests/` directory mirroring the package structure
- Run tests with pytest:
  ```bash
  python -m pytest tests/
  ```
- For coverage reporting:
  ```bash
  python -m pytest tests/ --cov=contexa_sdk
  ```

## Documentation

- Follow the [Documentation Standards](docs/DOCUMENTATION_STANDARDS.md)
- Update relevant README files for significant changes
- Include examples for new features
- Keep API documentation up-to-date

## Issue Reporting

- Use the GitHub issue tracker to report bugs or request features
- Check if the issue has already been reported
- Include details about your environment (OS, Python version, etc.)
- For bugs, include steps to reproduce the issue
- For feature requests, explain the use case and benefits

Thank you for contributing to Contexa SDK! Your efforts help make the project better for everyone. 