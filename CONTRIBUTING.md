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

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to help us maintain a healthy and inclusive community.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip
- git

### Setup

1. Fork the repository on GitHub
2. Clone your fork:
   ```
   git clone https://github.com/YOUR_USERNAME/contexa_sdk.git
   cd contexa_sdk
   ```
3. Install development dependencies:
   ```
   pip install -e ".[dev,test]"
   ```

## Development Workflow

1. Create a branch for your work:
   ```
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following our coding standards (see below)

3. Add tests for your changes

4. Run tests to make sure everything passes:
   ```
   pytest
   ```

5. Commit your changes following our commit message guidelines

6. Push your branch and submit a pull request

## Coding Standards

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use [type hints](https://docs.python.org/3/library/typing.html) for all function parameters and return values
- Document all functions, classes, and modules using [Google style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
- Keep lines to a maximum of 88 characters (we use Black formatting)
- Use meaningful variable names and avoid abbreviations
- Run `black` and `isort` before committing changes

### Testing

- Write unit tests for all new functionality
- Use pytest fixtures for common test setups
- Mock external dependencies where appropriate
- Test both success and failure cases
- Aim for 90% or higher code coverage for new code

### Documentation

- Update documentation for any new features or changes to existing features
- Keep README.md and framework compatibility docs up to date
- Include examples for new features

## Framework Adapter Guidelines

When working on framework adapters, follow these guidelines:

1. **Standardized Interface**: All adapters must implement the same core interface methods:
   - `create_model()` - Create a model compatible with the framework
   - `create_tool()` - Create a tool compatible with the framework
   - `create_agent()` - Create an agent using the framework

2. **Error Handling**: All adapters should catch framework-specific errors and raise consistent Contexa SDK errors with helpful messages.

3. **Dependency Management**: Use try/except imports for adapter dependencies to allow the SDK to function without all adapters installed.

4. **Conversion Functions**: Provide helper functions to convert between Contexa SDK types and framework-specific types.

5. **Cross-Framework Compatibility**: Ensure adapters can pass data between frameworks through the Contexa SDK standard formats.

6. **Tests**: Write comprehensive tests that verify both functionality and cross-framework compatibility.

## Pull Request Process

1. Update the CHANGELOG.md with details of your changes
2. Make sure all tests pass locally
3. Ensure your code follows our coding standards
4. Update documentation as needed
5. Submit the pull request with a clear description of the changes
6. Address any feedback from code reviews

## Commit Message Guidelines

We follow a simplified version of [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - A new feature
- `fix:` - A bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code changes that neither fix bugs nor add features
- `style:` - Changes that don't affect code function (formatting, whitespace)
- `chore:` - Other changes that don't modify src or test files

Example: `feat: add support for CrewAI framework`

## Release Process

Contexa SDK follows [Semantic Versioning](https://semver.org/):

- MAJOR version for incompatible API changes
- MINOR version for backward-compatible functionality
- PATCH version for backward-compatible bug fixes

The release process is handled by the maintainers and involves:
1. Updating CHANGELOG.md
2. Creating a version tag
3. Building and publishing the package

## License

By contributing to Contexa SDK, you agree that your contributions will be licensed under the project's MIT License.

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