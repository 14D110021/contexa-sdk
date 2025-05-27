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
from .integration import MCPIntegration, integrate_mcp_server_with_agent, create_multi_agent_mcp_server
# from .discovery import MCPServerDiscovery, MCPRegistry  # TODO: Implement in Sprint 5
# from .proxy import MCPToolProxy, MCPResourceProxy, MCPPromptProxy  # TODO: Implement in Sprint 3

__all__ = [
    'MCPClient',
    'MCPClientConfig',
    'MCPIntegration',
    'integrate_mcp_server_with_agent',
    'create_multi_agent_mcp_server',
    # 'MCPServerDiscovery',  # TODO: Implement in Sprint 5
    # 'MCPRegistry',  # TODO: Implement in Sprint 5
    # 'MCPToolProxy',  # TODO: Implement in Sprint 3
    # 'MCPResourceProxy',  # TODO: Implement in Sprint 3
    # 'MCPPromptProxy',  # TODO: Implement in Sprint 3
] 