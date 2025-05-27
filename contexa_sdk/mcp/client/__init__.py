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
from .proxy import (
    MCPProxy, MCPProxyConfig, MCPProxyError, MCPConnectionError, 
    MCPTimeoutError, MCPServerError, MCPToolProxy, MCPResourceProxy, 
    MCPPromptProxy, MCPResource, MCPPromptTemplate
)
from .proxy_factory import MCPProxyFactory, MCPProxyManager, create_mcp_proxy_factory
# from .discovery import MCPServerDiscovery, MCPRegistry  # TODO: Implement in Sprint 5

__all__ = [
    'MCPClient',
    'MCPClientConfig',
    'MCPIntegration',
    'integrate_mcp_server_with_agent',
    'create_multi_agent_mcp_server',
    
    # Proxy components - ✅ IMPLEMENTED in Sprint 3
    'MCPProxy',
    'MCPProxyConfig',
    'MCPProxyError',
    'MCPConnectionError',
    'MCPTimeoutError', 
    'MCPServerError',
    'MCPToolProxy',
    'MCPResourceProxy',
    'MCPPromptProxy',
    'MCPResource',
    'MCPPromptTemplate',
    'MCPProxyFactory',
    'MCPProxyManager',
    'create_mcp_proxy_factory',
    
    # 'MCPServerDiscovery',  # TODO: Implement in Sprint 5
    # 'MCPRegistry',  # TODO: Implement in Sprint 5
] 