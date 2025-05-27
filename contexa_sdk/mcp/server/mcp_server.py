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
from .handlers import (
    ResourceHandler, ToolHandler, PromptHandler, SamplingHandler,
    create_handlers, MCPHandler
)

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
        
        # Feature handlers
        self.handlers: Dict[str, MCPHandler] = create_handlers(self.config.__dict__)
        
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
        
        # Resource handlers
        self.protocol.register_request_handler("resources/list", self._handle_list_resources)
        self.protocol.register_request_handler("resources/read", self._handle_read_resource)
        self.protocol.register_request_handler("resources/subscribe", self._handle_subscribe_resource)
        self.protocol.register_request_handler("resources/unsubscribe", self._handle_unsubscribe_resource)
        
        # Prompt handlers
        self.protocol.register_request_handler("prompts/list", self._handle_list_prompts)
        self.protocol.register_request_handler("prompts/get", self._handle_get_prompt)
        
        # Sampling handlers
        self.protocol.register_request_handler("sampling/createMessage", self._handle_create_message)
    
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
        tool_handler = self.handlers["tool"]
        tools = await tool_handler.list_tools()
        return {"tools": tools}
    
    async def _handle_call_tool(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle tools/call request."""
        params = request.params or {}
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        tool_handler = self.handlers["tool"]
        return await tool_handler.call_tool(tool_name, arguments)
    
    async def _handle_list_resources(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle resources/list request."""
        resource_handler = self.handlers["resource"]
        resources = await resource_handler.list_resources()
        return {"resources": resources}
    
    async def _handle_read_resource(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle resources/read request."""
        params = request.params or {}
        uri = params.get("uri")
        
        if not uri:
            raise ValueError("Missing required parameter: uri")
        
        resource_handler = self.handlers["resource"]
        return await resource_handler.read_resource(uri)
    
    async def _handle_subscribe_resource(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle resources/subscribe request."""
        params = request.params or {}
        uri = params.get("uri")
        
        if not uri:
            raise ValueError("Missing required parameter: uri")
        
        # Use request ID as client ID for simplicity
        client_id = str(request.id)
        
        resource_handler = self.handlers["resource"]
        await resource_handler.subscribe_to_resource(client_id, uri)
        
        return {"success": True}
    
    async def _handle_unsubscribe_resource(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle resources/unsubscribe request."""
        params = request.params or {}
        uri = params.get("uri")
        
        if not uri:
            raise ValueError("Missing required parameter: uri")
        
        # Use request ID as client ID for simplicity
        client_id = str(request.id)
        
        resource_handler = self.handlers["resource"]
        await resource_handler.unsubscribe_from_resource(client_id, uri)
        
        return {"success": True}
    
    async def _handle_list_prompts(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle prompts/list request."""
        prompt_handler = self.handlers["prompt"]
        prompts = await prompt_handler.list_prompts()
        return {"prompts": prompts}
    
    async def _handle_get_prompt(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle prompts/get request."""
        params = request.params or {}
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            raise ValueError("Missing required parameter: name")
        
        prompt_handler = self.handlers["prompt"]
        return await prompt_handler.get_prompt(name, arguments)
    
    async def _handle_create_message(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle sampling/createMessage request."""
        params = request.params or {}
        messages = params.get("messages", [])
        model_preferences = params.get("modelPreferences")
        system_prompt = params.get("systemPrompt")
        include_context = params.get("includeContext", "none")
        temperature = params.get("temperature")
        max_tokens = params.get("maxTokens")
        stop_sequences = params.get("stopSequences")
        
        sampling_handler = self.handlers["sampling"]
        return await sampling_handler.create_message(
            messages=messages,
            model_preferences=model_preferences,
            system_prompt=system_prompt,
            include_context=include_context,
            temperature=temperature,
            max_tokens=max_tokens,
            stop_sequences=stop_sequences
        )
    
    async def register_agent(self, agent: ContexaAgent, name: Optional[str] = None):
        """Register a Contexa agent with the MCP server."""
        agent_name = name or agent.name or f"agent_{len(self.agents)}"
        self.agents[agent_name] = agent
        
        # Register agent's tools with the tool handler
        tool_handler = self.handlers["tool"]
        for tool in agent.tools:
            self.tools[tool.name] = tool  # Keep for backward compatibility
            await tool_handler.register_tool(tool)
        
        logger.info(f"Registered agent: {agent_name} with {len(agent.tools)} tools")
    
    async def register_tool(self, tool: ContexaTool):
        """Register a standalone tool with the MCP server."""
        self.tools[tool.name] = tool  # Keep for backward compatibility
        
        tool_handler = self.handlers["tool"]
        await tool_handler.register_tool(tool)
        
        logger.info(f"Registered tool: {tool.name}")
    
    async def start(self):
        """Start the MCP server."""
        if self.running:
            logger.warning("Server is already running")
            return
        
        logger.info(f"Starting MCP server: {self.config.name}")
        
        try:
            # Initialize handlers
            for handler_name, handler in self.handlers.items():
                await handler.initialize()
                logger.debug(f"Initialized {handler_name} handler")
            
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
        
        # Cleanup handlers
        for handler_name, handler in self.handlers.items():
            await handler.cleanup()
            logger.debug(f"Cleaned up {handler_name} handler")
        
        logger.info("MCP server stopped")
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information for handlers and clients."""
        return {
            "name": self.config.name,
            "version": self.config.version,
            "description": self.config.description,
            "running": self.running,
            "initialized": self.initialized,
            "agent_count": len(self.agents),
            "tool_count": len(self.tools),
            "capabilities": self.capabilities.to_dict() if self.capabilities else {}
        }
    
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


async def create_mcp_server_for_agent(
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
    await server.register_agent(agent)
    
    return server