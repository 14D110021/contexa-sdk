# Documentation Standards for Contexa SDK

This document outlines the standards for documenting the Contexa SDK codebase to ensure consistency and clarity.

## Code Documentation

### Python Docstrings

Use Google-style docstrings for all Python modules, classes, methods, and functions:

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """Short description of the function.
    
    Longer description explaining more details about the function,
    its purpose, and any important information.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of the return value
        
    Raises:
        ExceptionType: Explanation of when this exception is raised
    """
```

For classes:

```python
class ClassName:
    """Short description of the class.
    
    Longer description explaining the purpose and behavior of the class.
    
    Attributes:
        attr1: Description of attr1
        attr2: Description of attr2
    """
```

### Type Annotations

- Use type annotations for all function parameters and return values
- Use `Optional[Type]` for parameters that can be None
- Use `Union[Type1, Type2]` for parameters that can be multiple types
- Use `Any` only when absolutely necessary
- For collections, specify the contained type (e.g., `List[str]`, `Dict[str, int]`)

## README Files

Each major component should have a dedicated README.md file:

1. **Overview**: Brief description of the component's purpose
2. **Installation**: How to install (if applicable)
3. **Usage**: Code examples showing basic usage
4. **API Reference**: Link to detailed API documentation
5. **Advanced Usage**: More complex examples (optional)

## Example Code

- All examples should be fully functional and tested
- Include imports and configuration setup
- Use realistic variable names and scenarios
- Add comments explaining key steps
- Show both basic and advanced usages where applicable

## Framework Adapter Documentation

For each framework adapter, document:

1. **Supported Framework Version**: Specify the minimum supported version
2. **Installation**: Required dependencies
3. **Object Mapping**: How Contexa objects map to framework objects
4. **Limitations**: Any known limitations or unsupported features
5. **Examples**: Working examples of conversion and usage

## Handoff Documentation

For handoff functionality, document:

1. **Supported Paths**: Which frameworks can hand off to which others
2. **Context Preservation**: How conversation context is preserved
3. **Error Handling**: How errors are handled and reported
4. **Examples**: Complete examples showing handoffs between frameworks

## API Reference

All public APIs should be documented with:

1. **Parameters**: All parameters with types and descriptions
2. **Return Values**: Types and descriptions
3. **Exceptions**: All exceptions that may be raised
4. **Examples**: At least one usage example

## Versioning and Compatibility

Document:

1. **Version Requirements**: Minimum versions of frameworks
2. **Breaking Changes**: Clearly mark breaking changes in release notes
3. **Deprecation Notices**: Add deprecation warnings in code and documentation

## Writing Style Guidelines

1. **Clear and Concise**: Use simple, direct language
2. **Active Voice**: Prefer active voice over passive
3. **Consistency**: Use consistent terminology throughout
4. **Examples**: Include examples for complex concepts
5. **Formatting**: Use proper Markdown formatting for readability

## Review Process

Documentation changes should:

1. Be reviewed by at least one team member
2. Include verification that examples work
3. Be checked for clarity and completeness
4. Adhere to these standards

---

By following these guidelines, we ensure the Contexa SDK documentation remains high-quality, consistent, and helpful for all users. 