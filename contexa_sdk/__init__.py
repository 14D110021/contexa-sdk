"""
Contexa SDK: A framework for standardized AI agent development and interoperability.

This framework enables "write once, run anywhere" agent development with
cross-framework compatibility, standardized tools, and powerful orchestration.
"""

__version__ = "0.1.0"
__author__ = "Rupesh Raj"

# Lazy imports to avoid circular dependencies
from contexa_sdk import core
from contexa_sdk import adapters
from contexa_sdk import orchestration
from contexa_sdk import mcp

__all__ = [
    'core',
    'adapters',
    'orchestration', 
    'mcp',
] 