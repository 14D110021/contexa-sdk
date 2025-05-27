# Contexa SDK Versioning Strategy

## Overview

This document outlines the versioning strategy for Contexa SDK to ensure consistent, predictable releases and clear communication of changes to users. The strategy follows semantic versioning principles while adding specific considerations for adapter modules and framework compatibility.

## Semantic Versioning

Contexa SDK follows [Semantic Versioning 2.0.0](https://semver.org/) with version numbers in the format of `MAJOR.MINOR.PATCH`:

1. **MAJOR** version changes when incompatible API changes are made
2. **MINOR** version changes when functionality is added in a backward-compatible manner
3. **PATCH** version changes when backward-compatible bug fixes are implemented

## Adapter Versioning

Since adapters are a critical component of the SDK, we implement additional versioning considerations:

### Adapter Version Tracking

Each adapter maintains its own internal version number using the format:
```python
__adapter_version__ = "X.Y.Z"
```

Where:
- **X**: Major adapter version (changes with breaking API changes)
- **Y**: Minor adapter version (changes with new features)
- **Z**: Patch adapter version (changes with bug fixes)

### Framework Compatibility Matrix

A framework compatibility matrix is maintained in `FRAMEWORK_COMPATIBILITY.md`, specifying:

- Minimum supported version of each framework
- Maximum tested version of each framework
- Known compatibility issues
- Feature support across framework versions

## Version Implementation

### Version Management

1. **Central Version Source**
   - The master version is defined in `contexa_sdk/__init__.py`:
   ```python
   __version__ = "0.1.0"
   ```
   - This is the single source of truth for the package version

2. **Adapter Version Tracking**
   - Each adapter module defines its internal version:
   ```python
   # In contexa_sdk/adapters/langchain.py
   __adapter_version__ = "0.1.0"
   ```

3. **Version Compatibility Checking**
   - Runtime version compatibility checking:
   ```python
   def check_framework_compatibility(framework_name, framework_version):
       """Check if the framework version is compatible with the adapter."""
       min_version = FRAMEWORK_COMPATIBILITY[framework_name]["min_version"]
       max_version = FRAMEWORK_COMPATIBILITY[framework_name]["max_version"]
       
       # Check compatibility and issue appropriate warnings/errors
   ```

## Release Process

### Version Bumping

1. For a new release:
   - Update `__version__` in `contexa_sdk/__init__.py`
   - Update affected adapter versions in their respective modules
   - Update `CHANGELOG.md` with detailed release notes
   - Update `FRAMEWORK_COMPATIBILITY.md` if framework compatibility changes

2. Automated version checks:
   - CI tests should verify version consistency
   - Version checks should be included in pre-commit hooks

### Release Notes Requirements

Release notes in `CHANGELOG.md` must include:

1. **Summary**: Brief description of the release
2. **Breaking Changes**: Detailed explanation of any API changes
3. **New Features**: Description of new functionality
4. **Bug Fixes**: List of resolved issues
5. **Adapter Updates**: Changes to specific adapters
6. **Framework Compatibility**: Updates to framework compatibility

## Deprecation Policy

1. **Feature Deprecation**:
   - Features are marked as deprecated before removal
   - Deprecation warnings are issued for at least one MINOR version before removal
   - Deprecated features are documented in `CHANGELOG.md`

2. **Deprecation Implementation**:
   ```python
   import warnings
   
   def deprecated_feature():
       warnings.warn(
           "deprecated_feature is deprecated and will be removed in version 0.2.0. "
           "Use new_feature instead.",
           DeprecationWarning,
           stacklevel=2
       )
       # Implementation
   ```

## Version Query API

Expose version information through a programmatic API:

```python
from contexa_sdk import version

# Get SDK version
sdk_version = version.get_version()

# Get adapter version
langchain_adapter_version = version.get_adapter_version("langchain")

# Check framework compatibility
is_compatible = version.check_compatibility("langchain", "0.1.0")
```

## Implementation Timeline

1. **Phase 1: Version Structure**
   - Add `__version__` to main package
   - Add `__adapter_version__` to each adapter
   - Create initial framework compatibility matrix

2. **Phase 2: Version Checking**
   - Implement framework compatibility checking
   - Add version query API
   - Create version consistency tests

3. **Phase 3: Automation**
   - Add version bumping to release scripts
   - Implement automated compatibility testing
   - Create documentation generation for version-specific features

## Conclusion

This versioning strategy ensures that Contexa SDK maintains clear and predictable versioning across releases, with special attention to adapter modules and framework compatibility. By following these guidelines, we can provide users with a stable and reliable development experience while continually improving the SDK. 