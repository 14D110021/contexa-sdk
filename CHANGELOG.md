# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite for runtime components
- Observability tests for metrics and tracing
- GitHub Actions CI/CD workflow
- PR and issue templates
- Cross-framework handoff tests
- Resource tracking tests
- Health monitoring tests
- Dedicated documentation for Google adapters
- Examples demonstrating both Google GenAI and ADK usage
- Tests for cross-framework compatibility with Google adapters

### Changed
- Standardized model handling across all adapters
- Improved error handling in all adapters
- Made CrewAI crew creation optional
- Updated OpenAI package references to use correct imports
- **Restructured Google adapters**: Properly separated Google GenAI and Google ADK implementations with clear namespacing
- Enhanced Google adapter interfaces with better error handling and synchronous wrappers
- Improved setup.py with explicit separate dependencies for Google GenAI and ADK

### Fixed
- Google adapter import statements
- CrewAI multi-agent support
- Framework version compatibility checks
- Adapter error handling for missing dependencies

## [0.1.0] - YYYY-MM-DD

### Added
- Initial release of Contexa SDK
- Core components (tools, models, agents)
- Multi-framework adapters (LangChain, CrewAI, OpenAI, Google ADK)
- Runtime system
- Observability features
- MCP integration
- Agent orchestration 