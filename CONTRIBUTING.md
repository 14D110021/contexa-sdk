# Contributing to Contexa SDK

Thank you for your interest in contributing to Contexa SDK! This document outlines the process for contributing to the project.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/rupeshrajdev/contexa_sdk.git
   cd contexa_sdk
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   pip install -e ".[all,dev]"
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Style

We follow PEP 8 guidelines with some modifications:
- Line length: 100 characters
- Use docstrings for all public methods and classes
- Use type hints wherever possible

## Testing

All new features should include tests. We use pytest for testing:

```bash
pytest tests/
```

For coverage reports:

```bash
pytest --cov=contexa_sdk tests/
```

## Submitting Changes

1. **Fork the repository** on GitHub.

2. **Create a feature branch** from the main branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** and commit them with clear, descriptive commit messages.

4. **Write or update tests** for the changes you made.

5. **Run the tests** to ensure they pass.

6. **Update documentation** if necessary.

7. **Submit a pull request** to the main branch of the original repository.

## Pull Request Process

1. Ensure your PR includes tests for new functionality.
2. Update documentation as needed.
3. Your PR should have a clear title and description.
4. Link any relevant issues in your PR description.
5. Wait for a code review by maintainers.

## Adding New Framework Support

If you want to add support for a new agent framework:

1. Create a new module in `contexa_sdk/adapters/[framework_name]/`
2. Implement the necessary conversion functions
3. Update the setup.py to include the new framework as an extra
4. Add tests in `tests/adapters/test_[framework_name].py`
5. Add documentation in `docs/multi_framework.md`

## Adding New Orchestration Features

When adding new orchestration features:

1. Follow existing patterns in the orchestration module
2. Ensure framework interoperability
3. Update documentation in `docs/orchestration.md`
4. Add examples in the `examples/` directory

## License

By contributing to Contexa SDK, you agree that your contributions will be licensed under the project's MIT License. 