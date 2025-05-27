"""
MCP Client implementation.

This module provides the primary MCPClient class that implements a complete
Model Context Protocol client, allowing Contexa agents to connect to and
consume capabilities from remote MCP servers.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
import httpx

logger = logging.getLogger(__name__)


@dataclass
class MCPClientConfig:
    """Configuration for MCP Client."""
    name: str = "Contexa MCP Client"
    version: str = "1.0.0"
    
    # Connection configuration
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Protocol configuration
    protocol_version: str = "2025-03-26"
    
    # Client capabilities
    supports_sampling: bool = True
    supports_roots: bool = False
    supports_logging: bool = True


class MCPClient:
    """
    Complete MCP Client implementation.
    
    This class provides a full implementation of the Model Context Protocol
    client specification, allowing connection to and consumption of MCP servers.
    """
    
    def __init__(self, config: Optional[MCPClientConfig] = None):
        self.config = config or MCPClientConfig()
        
        # Connection state
        self.connected = False
        self.initialized = False
        self.server_info: Optional[Dict[str, Any]] = None
        self.server_capabilities: Optional[Dict[str, Any]] = None
        
        # HTTP client for remote connections
        self.http_client: Optional[httpx.AsyncClient] = None
        
        # Cached server data
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._resources_cache: Optional[List[Dict[str, Any]]] = None
        self._prompts_cache: Optional[List[Dict[str, Any]]] = None
    
    async def connect(self, server_url: str, auth: Optional[Dict[str, Any]] = None):
        """Connect to an MCP server."""
        if self.connected:
            await self.disconnect()
        
        logger.info(f"Connecting to MCP server: {server_url}")
        
        # Create HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers={"Content-Type": "application/json"}
        )
        
        # Add authentication if provided
        if auth:
            if auth.get("type") == "bearer":
                self.http_client.headers["Authorization"] = f"Bearer {auth['token']}"
            elif auth.get("type") == "basic":
                self.http_client.auth = (auth["username"], auth["password"])
        
        self.server_url = server_url
        
        try:
            # Initialize connection
            await self._initialize_connection()
            self.connected = True
            logger.info("Successfully connected to MCP server")
            
        except Exception as e:
            logger.exception("Failed to connect to MCP server")
            await self.disconnect()
            raise
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if not self.connected:
            return
        
        logger.info("Disconnecting from MCP server")
        
        self.connected = False
        self.initialized = False
        self.server_info = None
        self.server_capabilities = None
        
        # Clear caches
        self._tools_cache = None
        self._resources_cache = None
        self._prompts_cache = None
        
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        
        logger.info("Disconnected from MCP server")
    
    async def _initialize_connection(self):
        """Initialize the MCP connection."""
        # Send initialize request
        client_capabilities = {
            "sampling": {} if self.config.supports_sampling else None,
            "roots": {"listChanged": True} if self.config.supports_roots else None,
            "logging": {} if self.config.supports_logging else None,
        }
        
        # Remove None values
        client_capabilities = {k: v for k, v in client_capabilities.items() if v is not None}
        
        init_request = {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {
                "protocolVersion": self.config.protocol_version,
                "capabilities": client_capabilities,
                "clientInfo": {
                    "name": self.config.name,
                    "version": self.config.version,
                }
            }
        }
        
        response = await self._send_request(init_request)
        
        if "error" in response:
            raise Exception(f"Initialization failed: {response['error']}")
        
        result = response.get("result", {})
        self.server_info = result.get("serverInfo", {})
        self.server_capabilities = result.get("capabilities", {})
        
        logger.info(f"Server info: {self.server_info}")
        logger.info(f"Server capabilities: {list(self.server_capabilities.keys())}")
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "initialized"
        }
        
        await self._send_notification(initialized_notification)
        self.initialized = True
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the MCP server."""
        if not self.http_client:
            raise RuntimeError("Not connected to server")
        
        try:
            response = await self.http_client.post(
                f"{self.server_url}/mcp",
                json=request
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code}")
            raise
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """Send a notification to the MCP server."""
        if not self.http_client:
            raise RuntimeError("Not connected to server")
        
        try:
            response = await self.http_client.post(
                f"{self.server_url}/mcp",
                json=notification
            )
            response.raise_for_status()
            
        except httpx.RequestError as e:
            logger.error(f"Notification failed: {e}")
            raise
    
    async def list_tools(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """List available tools from the server."""
        if not self.connected or not self.initialized:
            raise RuntimeError("Not connected to server")
        
        if not force_refresh and self._tools_cache is not None:
            return self._tools_cache
        
        if "tools" not in self.server_capabilities:
            return []
        
        request = {
            "jsonrpc": "2.0",
            "id": "list_tools",
            "method": "tools/list"
        }
        
        response = await self._send_request(request)
        
        if "error" in response:
            raise Exception(f"Failed to list tools: {response['error']}")
        
        tools = response.get("result", {}).get("tools", [])
        self._tools_cache = tools
        
        logger.debug(f"Listed {len(tools)} tools from server")
        return tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the server."""
        if not self.connected or not self.initialized:
            raise RuntimeError("Not connected to server")
        
        if "tools" not in self.server_capabilities:
            raise RuntimeError("Server does not support tools")
        
        request = {
            "jsonrpc": "2.0",
            "id": f"call_tool_{name}",
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        
        response = await self._send_request(request)
        
        if "error" in response:
            raise Exception(f"Tool call failed: {response['error']}")
        
        return response.get("result", {})
    
    async def list_resources(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """List available resources from the server."""
        if not self.connected or not self.initialized:
            raise RuntimeError("Not connected to server")
        
        if not force_refresh and self._resources_cache is not None:
            return self._resources_cache
        
        if "resources" not in self.server_capabilities:
            return []
        
        request = {
            "jsonrpc": "2.0",
            "id": "list_resources",
            "method": "resources/list"
        }
        
        response = await self._send_request(request)
        
        if "error" in response:
            raise Exception(f"Failed to list resources: {response['error']}")
        
        resources = response.get("result", {}).get("resources", [])
        self._resources_cache = resources
        
        logger.debug(f"Listed {len(resources)} resources from server")
        return resources
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource from the server."""
        if not self.connected or not self.initialized:
            raise RuntimeError("Not connected to server")
        
        if "resources" not in self.server_capabilities:
            raise RuntimeError("Server does not support resources")
        
        request = {
            "jsonrpc": "2.0",
            "id": f"read_resource_{uri}",
            "method": "resources/read",
            "params": {
                "uri": uri
            }
        }
        
        response = await self._send_request(request)
        
        if "error" in response:
            raise Exception(f"Resource read failed: {response['error']}")
        
        return response.get("result", {})
    
    async def list_prompts(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """List available prompts from the server."""
        if not self.connected or not self.initialized:
            raise RuntimeError("Not connected to server")
        
        if not force_refresh and self._prompts_cache is not None:
            return self._prompts_cache
        
        if "prompts" not in self.server_capabilities:
            return []
        
        request = {
            "jsonrpc": "2.0",
            "id": "list_prompts",
            "method": "prompts/list"
        }
        
        response = await self._send_request(request)
        
        if "error" in response:
            raise Exception(f"Failed to list prompts: {response['error']}")
        
        prompts = response.get("result", {}).get("prompts", [])
        self._prompts_cache = prompts
        
        logger.debug(f"Listed {len(prompts)} prompts from server")
        return prompts
    
    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a prompt from the server."""
        if not self.connected or not self.initialized:
            raise RuntimeError("Not connected to server")
        
        if "prompts" not in self.server_capabilities:
            raise RuntimeError("Server does not support prompts")
        
        params = {"name": name}
        if arguments:
            params["arguments"] = arguments
        
        request = {
            "jsonrpc": "2.0",
            "id": f"get_prompt_{name}",
            "method": "prompts/get",
            "params": params
        }
        
        response = await self._send_request(request)
        
        if "error" in response:
            raise Exception(f"Prompt get failed: {response['error']}")
        
        return response.get("result", {})
    
    async def create_sampling_message(
        self,
        messages: List[Dict[str, Any]],
        model_preferences: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        include_context: str = "none",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Request sampling from the server."""
        if not self.connected or not self.initialized:
            raise RuntimeError("Not connected to server")
        
        if "sampling" not in self.server_capabilities:
            raise RuntimeError("Server does not support sampling")
        
        params = {
            "messages": messages,
            "includeContext": include_context,
        }
        
        if model_preferences:
            params["modelPreferences"] = model_preferences
        if system_prompt:
            params["systemPrompt"] = system_prompt
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["maxTokens"] = max_tokens
        if stop_sequences:
            params["stopSequences"] = stop_sequences
        
        request = {
            "jsonrpc": "2.0",
            "id": "create_sampling_message",
            "method": "sampling/createMessage",
            "params": params
        }
        
        response = await self._send_request(request)
        
        if "error" in response:
            raise Exception(f"Sampling failed: {response['error']}")
        
        return response.get("result", {})
    
    async def ping(self) -> bool:
        """Ping the server to check connectivity."""
        if not self.connected:
            return False
        
        try:
            request = {
                "jsonrpc": "2.0",
                "id": "ping",
                "method": "ping"
            }
            
            response = await self._send_request(request)
            return "error" not in response
            
        except Exception:
            return False
    
    def get_server_info(self) -> Optional[Dict[str, Any]]:
        """Get server information."""
        return self.server_info
    
    def get_server_capabilities(self) -> Optional[Dict[str, Any]]:
        """Get server capabilities."""
        return self.server_capabilities
    
    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self.connected and self.initialized 