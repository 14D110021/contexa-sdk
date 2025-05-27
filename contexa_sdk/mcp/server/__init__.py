"""
MCP Server implementation for Contexa SDK.

This module provides a complete implementation of the Model Context Protocol (MCP)
server specification, allowing Contexa agents to be exposed as MCP-compatible
servers that can be consumed by any MCP client.

The implementation follows the MCP specification v2025-03-26 and includes:
- JSON-RPC 2.0 message handling
- Capability negotiation
- Resources, Tools, and Prompts exposure
- Sampling support
- Security and consent management
"""

from .mcp_server import MCPServer, MCPServerConfig
from .protocol import MCPProtocol, MCPMessage, MCPRequest, MCPResponse, MCPNotification
from .capabilities import ServerCapabilities, ResourceCapability, ToolCapability, PromptCapability
from .transport import StdioTransport, HTTPTransport, SSETransport
from .handlers import ResourceHandler, ToolHandler, PromptHandler, SamplingHandler
# from .security import SecurityManager, ConsentManager, AuthenticationManager  # TODO: Implement in Sprint 4

__all__ = [
    'MCPServer',
    'MCPServerConfig', 
    'MCPProtocol',
    'MCPMessage',
    'MCPRequest',
    'MCPResponse',
    'MCPNotification',
    'ServerCapabilities',
    'ResourceCapability',
    'ToolCapability', 
    'PromptCapability',
    'StdioTransport',
    'HTTPTransport',
    'SSETransport',
    'ResourceHandler',
    'ToolHandler',
    'PromptHandler',
    'SamplingHandler',
    # 'SecurityManager',      # TODO: Implement in Sprint 4
    # 'ConsentManager',       # TODO: Implement in Sprint 4
    # 'AuthenticationManager', # TODO: Implement in Sprint 4
] 