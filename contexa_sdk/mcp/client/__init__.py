"""
MCP Client implementation for Contexa SDK.

This module provides a complete implementation of the Model Context Protocol (MCP)
client specification, allowing Contexa agents to consume remote MCP servers
and integrate their capabilities.

The implementation follows the MCP specification v2025-03-26 and includes:
- JSON-RPC 2.0 message handling
- Capability negotiation
- Resource, Tool, and Prompt consumption
- Sampling requests
- Multiple transport support
"""

from .mcp_client import MCPClient, MCPClientConfig
from .discovery import MCPServerDiscovery, MCPRegistry
from .integration import MCPIntegration, integrate_mcp_server_with_agent
from .proxy import MCPToolProxy, MCPResourceProxy, MCPPromptProxy

__all__ = [
    'MCPClient',
    'MCPClientConfig',
    'MCPServerDiscovery',
    'MCPRegistry',
    'MCPIntegration',
    'integrate_mcp_server_with_agent',
    'MCPToolProxy',
    'MCPResourceProxy',
    'MCPPromptProxy',
] 