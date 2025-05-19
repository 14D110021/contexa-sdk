# Developer Guidelines for Contexa SDK

This document provides guidelines for developers working on or contributing to the Contexa SDK codebase, with special focus on the adapter modules.

## General Principles

1. **Consistency**: Follow established patterns in the codebase
2. **Testability**: Write code that can be tested without external dependencies
3. **Documentation**: Document all public interfaces thoroughly
4. **Error Handling**: Provide clear, actionable error messages
5. **Backward Compatibility**: Avoid breaking changes where possible

## Adapter Development Guidelines

### Structure

- Each framework adapter should be in its own module or package
- Complex adapters should be organized in subpackages (e.g., `google/`)
- Use `__init__.py` to provide a clean, consistent public API

### Function Naming

- Use clear, descriptive names that indicate the adapter's framework
- For adapters with multiple implementations (like Google's GenAI and ADK):
  - Use prefixed function names (e.g., `genai_tool`, `adk_tool`)
  - Provide backward compatibility aliases where appropriate

### Error Handling

- Check for required dependencies and provide helpful messages if missing
- Validate input parameters before attempting conversion
- Wrap framework-specific errors with more context when appropriate
- Include suggestions for resolution in error messages

### Testing

- Write tests that don't require the actual framework to be installed
- Use mock implementations for testing core functionality
- Test both happy paths and error conditions
- For cross-framework tests, test with minimal framework subsets

### Documentation

- Document both adapter-specific behavior and framework requirements
- Include installation instructions with version requirements
- Provide examples showing typical usage patterns
- Document any limitations or framework-specific behaviors

## Google Adapter-Specific Guidelines

### Separation of Concerns

- Keep Google GenAI and Google ADK implementations clearly separated
- Use the package structure to enforce separation: 
  - `google/genai.py` for GenAI implementation
  - `google/adk.py` for ADK implementation
  - `google/converter.py` for shared functionality

### Naming Conventions

- Use `genai_*` prefix for Google Generative AI (Gemini) functions
- Use `adk_*` prefix for Google Agent Development Kit functions
- Export non-prefixed names for backward compatibility where appropriate

### Dependencies

- Make dependencies optional by using try/except for imports
- Provide mock implementations for testing without dependencies
- Document which dependencies are needed for which functionality

### Async/Sync Support

- Implement async functions as the primary interface
- Provide synchronous wrappers for better usability
- Document async behavior and any limitations

## Contributing New Adapters

When contributing a new adapter, ensure:

1. **Core Coverage**: Implement all core conversions (tool, model, agent)
2. **Documentation**: Add adapter-specific documentation
3. **Testing**: Create tests for the adapter's functionality
4. **Examples**: Provide usage examples
5. **Setup**: Update setup.py with appropriate dependencies

## Version Compatibility

- Document which adapter versions work with which framework versions
- Test with minimum and recommended framework versions
- Provide clear upgrade paths when breaking changes are necessary

## Documentation Standards

Follow the [Documentation Standards](docs/DOCUMENTATION_STANDARDS.md) document for specific guidelines on:

- Docstring format and requirements
- README structure
- Example code guidelines
- API reference documentation

## Pull Request Guidelines

When submitting a PR:

1. Ensure all tests pass
2. Update documentation as needed
3. Follow the coding style of the project
4. Include a description of the changes
5. Reference any related issues

## Release Process

1. Update version numbers according to semantic versioning
2. Update CHANGELOG.md with notable changes
3. Create a release branch
4. Build and test the distribution
5. Create a tagged release
6. Deploy to PyPI 