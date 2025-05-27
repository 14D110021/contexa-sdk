"""
Main MCP Server implementation.

This module provides the primary MCPServer class that implements a complete
Model Context Protocol server, integrating protocol handling, transport
management, capability negotiation, and feature handlers.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import ContexaTool

from .protocol import MCPProtocol, MCPRequest, MCPResponse, MCPNotification, MCPErrorCode
from .capabilities import ServerCapabilities, create_default_server_capabilities
from .transport import MCPTransport, create_transport

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for MCP Server."""
    name: str = "Contexa MCP Server"
    version: str = "1.0.0"
    description: str = "MCP Server powered by Contexa SDK"
    
    # Transport configuration
    transport_type: str = "stdio"  # "stdio", "http", "sse"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Capability configuration
    capabilities: Optional[ServerCapabilities] = None
    
    # Security configuration
    require_authentication: bool = False
    allowed_origins: List[str] = field(default_factory=list)
    rate_limit_requests_per_minute: int = 100
    
    # Feature configuration
    enable_sampling: bool = True
    enable_resource_subscriptions: bool = False
    enable_logging: bool = True
    
    # Protocol configuration
    protocol_version: str = "2025-03-26"
    max_message_size: int = 1024 * 1024  # 1MB
    request_timeout: float = 30.0


class MCPServer:
    """
    Complete MCP Server implementation.
    
    This class provides a full implementation of the Model Context Protocol
    server specification, allowing Contexa agents and teams to be exposed
    as MCP-compatible servers.
    """
    
    def __init__(self, config: Optional[MCPServerConfig] = None):
        self.config = config or MCPServerConfig()
        
        # Core components
        self.protocol = MCPProtocol()
        self.transport: Optional[MCPTransport] = None
        self.capabilities: ServerCapabilities = self.config.capabilities or create_default_server_capabilities()
        
        # State
        self.running = False
        self.initialized = False
        self.client_info: Optional[Dict[str, Any]] = None
        self.negotiated_capabilities: Optional[ServerCapabilities] = None
        
        # Registered agents
        self.agents: Dict[str, ContexaAgent] = {}
        self.tools: Dict[str, ContexaTool] = {}
        
        # Setup protocol handlers
        self._setup_protocol_handlers()
    
    def _setup_protocol_handlers(self):
        """Set up protocol message handlers."""
        # Core protocol handlers
        self.protocol.register_request_handler("initialize", self._handle_initialize)
        self.protocol.register_notification_handler("initialized", self._handle_initialized)
        self.protocol.register_request_handler("ping", self._handle_ping)
        
        # Tool handlers
        self.protocol.register_request_handler("tools/list", self._handle_list_tools)
        self.protocol.register_request_handler("tools/call", self._handle_call_tool)
    
    async def _handle_initialize(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle initialization request."""
        try:
            params = request.params or {}
            
            # Store client info
            self.client_info = params.get("clientInfo", {})
            
            # Negotiate capabilities
            client_capabilities = params.get("capabilities", {})
            self.negotiated_capabilities = self.capabilities
            
            # Prepare server info
            server_info = {
                "name": self.config.name,
                "version": self.config.version,
                "description": self.config.description,
            }
            
            # Return initialization response
            return {
                "protocolVersion": self.config.protocol_version,
                "capabilities": self.negotiated_capabilities.to_dict(),
                "serverInfo": server_info,
            }
            
        except Exception as e:
            logger.exception("Error during initialization")
            raise
    
    async def _handle_initialized(self, notification: MCPNotification):
        """Handle initialized notification."""
        self.initialized = True
        logger.info("MCP server initialized successfully")
    
    async def _handle_ping(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle ping request."""
        return {"pong": True}
    
    async def _handle_list_tools(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools = []
        for tool_name, tool in self.tools.items():
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.parameters_schema if hasattr(tool, 'parameters_schema') else {}
            })
        
        return {"tools": tools}
    
    async def _handle_call_tool(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle tools/call request."""
        params = request.params or {}
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            raise Exception(f"Tool '{tool_name}' not found")
        
        tool = self.tools[tool_name]
        
        try:
            # Execute the tool
            result = await tool.execute(arguments)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ]
            }
        except Exception as e:
            logger.exception(f"Error executing tool {tool_name}")
            return {
                "content": [
                    {
                        "type": "text", 
                        "text": f"Error executing tool: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    def register_agent(self, agent: ContexaAgent, name: Optional[str] = None):
        """Register a Contexa agent with the MCP server."""
        agent_name = name or agent.name or f"agent_{len(self.agents)}"
        self.agents[agent_name] = agent
        
        # Register agent's tools
        for tool in agent.tools:
            self.tools[tool.name] = tool
        
        logger.info(f"Registered agent: {agent_name}")
    
    def register_tool(self, tool: ContexaTool):
        """Register a standalone tool with the MCP server."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    async def start(self):
        """Start the MCP server."""
        if self.running:
            logger.warning("Server is already running")
            return
        
        logger.info(f"Starting MCP server: {self.config.name}")
        
        try:
            # Create and configure transport
            self.transport = create_transport(
                self.config.transport_type,
                self.protocol,
                host=self.config.host,
                port=self.config.port
            )
            
            # Set message handler
            self.transport.set_message_handler(self.protocol.handle_message)
            
            # Start transport
            await self.transport.start()
            
            self.running = True
            
            logger.info(f"MCP server started successfully on {self.config.transport_type}")
            
        except Exception as e:
            logger.exception("Failed to start MCP server")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the MCP server."""
        if not self.running:
            return
        
        logger.info("Stopping MCP server")
        
        self.running = False
        self.initialized = False
        
        if self.transport:
            await self.transport.stop()
            self.transport = None
        
        logger.info("MCP server stopped")
    
    async def run(self):
        """Run the MCP server (blocking)."""
        await self.start()
        
        try:
            # Keep running until stopped
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.stop()


def create_mcp_server_for_agent(
    agent: ContexaAgent,
    transport_type: str = "stdio",
    **kwargs
) -> MCPServer:
    """Create an MCP server for a single agent."""
    config = MCPServerConfig(
        name=f"MCP Server for {agent.name}",
        description=f"MCP server exposing {agent.name}",
        transport_type=transport_type,
        **kwargs
    )
    
    server = MCPServer(config)
    server.register_agent(agent)
    
    return server