# Cleanup Tasks for Contexa SDK

This document tracks cleanup tasks that should be performed before the next release, organized by priority.

## High Priority (Before Next Minor Release)

### Google Adapters

- [ ] Remove deprecated files:
  - [ ] `contexa_sdk/adapters/google_genai.py` - Now moved to `contexa_sdk/adapters/google/genai.py`
  - [ ] `contexa_sdk/adapters/google_adk.py` - Now moved to `contexa_sdk/adapters/google/adk.py`

### Documentation

- [ ] Update API documentation to reflect the new Google adapter structure
- [ ] Add Google adapter section to main README.md
- [ ] Ensure installation instructions clearly explain optional dependencies

## Medium Priority (Before Next Major Release)

### API Improvements

- [ ] Add deprecation warnings to backward compatibility aliases
- [ ] Standardize naming conventions across all adapters
- [ ] Create consistent error handling patterns across frameworks

### File Organization

- [ ] Consider moving other adapters to directory-based structure:
  - [ ] `contexa_sdk/adapters/langchain.py` → `contexa_sdk/adapters/langchain/`
  - [ ] `contexa_sdk/adapters/crewai.py` → `contexa_sdk/adapters/crewai/`
  - [ ] `contexa_sdk/adapters/openai.py` → `contexa_sdk/adapters/openai/`

### Testing

- [ ] Add tests specifically for backward compatibility of deprecated paths
- [ ] Create comprehensive tests for error scenarios
- [ ] Set up dependency-optional test configurations

## Lower Priority (Ongoing Improvements)

### Documentation

- [ ] Update all examples to use new import patterns
- [ ] Create documentation linking model architectures between frameworks
- [ ] Add more advanced examples showing cross-framework integration

### Dependencies

- [ ] Update `setup.py` to clearly separate optional dependencies
- [ ] Create tests that verify that dependency errors are handled gracefully
- [ ] Document version compatibility requirements for all supported frameworks

### Code Quality

- [ ] Implement consistent docstring format across all modules
- [ ] Add type hints to all public interfaces
- [ ] Add performance benchmarks for critical operations

## Release Preparation Tasks

- [ ] Create CHANGELOG.md for tracking version changes
- [ ] Establish version compatibility matrix
- [ ] Update all version numbers before release
- [ ] Create release branch and tag structure 