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
- Migration guide for Google adapters (`docs/google_adapter_migration.md`)
- Example showing migration from old to new Google adapter structure
- Comprehensive docstrings for both Google GenAI and ADK adapters
- Complete integration tests for Google adapter cross-framework compatibility
- End-to-end workflow tests combining Google GenAI and ADK with other frameworks
- Updated installation documentation for separate Google adapter options in README.md and FRAMEWORK_COMPATIBILITY.md
- Comprehensive docstrings for all adapter modules (base.py, langchain.py, crewai.py, openai.py)
- Versioning strategy documentation and implementation (`docs/versioning_strategy.md`)
- Version utility module with compatibility checking features (`contexa_sdk/version.py`)
- Adapter-specific version tracking for all adapter modules
- Comprehensive docstrings for all runtime module components (agent_runtime.py, health_monitoring.py, etc.)
- Enhanced documentation for observability components with examples and usage patterns
- Detailed docstrings for deployment module (builder.py, deployer.py, mcp_generator.py)
- Improved CLI module documentation with command-specific examples and parameter details
- Module-level documentation in all __init__.py files explaining component relationships
- Added rich examples in docstrings demonstrating usage patterns throughout the SDK
- Standardized documentation format following Google style across all SDK components
- **Phase 5: CI/CD Pipeline Implementation** - Comprehensive automation workflows
  - Version checking and compatibility testing across Python 3.8-3.11
  - Framework-specific adapter compatibility testing
  - Cross-framework integration testing
  - MCP integration testing with code generation, building, and deployment validation
  - Performance benchmarking for agent creation, tool registration, and adapter conversion
  - Memory profiling and load testing capabilities
  - Automated release workflow with version validation, package building, and PyPI publishing
  - Enhanced documentation building with Sphinx integration
  - Security scanning with safety and bandit tools
- **Phase 6: MCP Integration Components** - Advanced Model Context Protocol implementation
  - Complete MCP protocol implementation following JSON-RPC 2.0 specification
  - Full MCP server implementation with capability negotiation and multi-transport support
  - Complete MCP client implementation for consuming remote MCP servers
  - MCP capabilities system with support for Resources, Tools, Prompts, and Sampling
  - Multiple transport implementations (stdio, HTTP, SSE) for flexible deployment
  - Production-ready MCP server and client with authentication and error handling
  - Foundation for MCP agent discovery, registry integration, and advanced features

### Changed
- Standardized model handling across all adapters
- Improved error handling in all adapters
- Made CrewAI crew creation optional
- Updated OpenAI package references to use correct imports
- **Restructured Google adapters**: Properly separated Google GenAI and Google ADK implementations with clear namespacing
- Enhanced Google adapter interfaces with better error handling and synchronous wrappers
- Improved setup.py with explicit separate dependencies for Google GenAI and ADK
- Added clear documentation about when to use each Google adapter type

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