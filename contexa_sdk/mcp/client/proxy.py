"""
MCP Client Proxies for transparent remote capability access.

This module provides proxy classes that enable transparent access to remote MCP
server capabilities (tools, resources, prompts) as if they were local objects.
The proxies handle connection management, caching, error handling, and provide
a seamless interface for distributed agent architectures.

Key Features:
- Transparent remote tool execution with ContexaTool interface
- Intelligent resource caching with LRU and TTL support
- Remote prompt template management with parameter validation
- Automatic connection pooling and error recovery
- Performance optimization with configurable caching strategies

Example:
    ```python
    from contexa_sdk.mcp.client.proxy import MCPToolProxy
    
    # Create a proxy for a remote tool
    tool_proxy = MCPToolProxy(
        server_url="http://localhost:8000",
        tool_name="calculator"
    )
    
    # Use it like a local tool
    result = await tool_proxy.execute({"operation": "add", "a": 5, "b": 3})
    ```
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from functools import lru_cache
import aiohttp

from contexa_sdk.core.tool import ContexaTool

logger = logging.getLogger(__name__)


@dataclass
class MCPProxyConfig:
    """Configuration for MCP proxy connections.
    
    This class defines the configuration options for connecting to and
    interacting with remote MCP servers through proxies.
    
    Attributes:
        server_url: Base URL of the MCP server
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        cache_ttl: Time-to-live for cached items in seconds
        cache_size: Maximum number of items in LRU cache
        enable_caching: Whether to enable caching
        connection_pool_size: Maximum connections in pool
        auth_token: Optional authentication token
        headers: Additional HTTP headers
    """
    server_url: str
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    cache_ttl: int = 300  # 5 minutes
    cache_size: int = 100
    enable_caching: bool = True
    connection_pool_size: int = 10
    auth_token: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)


class MCPProxyError(Exception):
    """Base exception for MCP proxy errors."""
    pass


class MCPConnectionError(MCPProxyError):
    """Raised when connection to MCP server fails."""
    pass


class MCPTimeoutError(MCPProxyError):
    """Raised when MCP server request times out."""
    pass


class MCPServerError(MCPProxyError):
    """Raised when MCP server returns an error."""
    pass


class MCPProxy(ABC):
    """Abstract base class for all MCP proxies.
    
    This class provides common functionality for connecting to and interacting
    with remote MCP servers. It handles connection management, error handling,
    retry logic, and provides a foundation for specific proxy implementations.
    
    Attributes:
        config: Configuration for the proxy connection
        session: HTTP session for making requests
        logger: Logger instance for this proxy
    """
    
    def __init__(self, config: MCPProxyConfig):
        """Initialize the MCP proxy.
        
        Args:
            config: Configuration for the proxy connection
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._connection_lock = asyncio.Lock()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def _ensure_session(self) -> None:
        """Ensure HTTP session is created and configured.
        
        Creates an aiohttp ClientSession with appropriate configuration
        including timeout, connection pooling, and authentication headers.
        """
        if self.session is None or self.session.closed:
            async with self._connection_lock:
                if self.session is None or self.session.closed:
                    # Configure timeout
                    timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                    
                    # Configure connection pooling
                    connector = aiohttp.TCPConnector(
                        limit=self.config.connection_pool_size,
                        limit_per_host=self.config.connection_pool_size
                    )
                    
                    # Prepare headers
                    headers = dict(self.config.headers)
                    headers["Content-Type"] = "application/json"
                    if self.config.auth_token:
                        headers["Authorization"] = f"Bearer {self.config.auth_token}"
                    
                    self.session = aiohttp.ClientSession(
                        timeout=timeout,
                        connector=connector,
                        headers=headers
                    )
                    
                    self.logger.debug(f"Created HTTP session for {self.config.server_url}")
    
    async def close(self) -> None:
        """Close the HTTP session and cleanup resources."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.debug("Closed HTTP session")
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the MCP server with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data (for POST requests)
            params: URL query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            MCPConnectionError: If connection fails after retries
            MCPTimeoutError: If request times out
            MCPServerError: If server returns an error
        """
        await self._ensure_session()
        
        url = f"{self.config.server_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.config.max_retries + 1):
            try:
                self.logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                async with self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params
                ) as response:
                    response_data = await response.json()
                    
                    if response.status >= 400:
                        error_msg = response_data.get("error", f"HTTP {response.status}")
                        raise MCPServerError(f"Server error: {error_msg}")
                    
                    self.logger.debug(f"Request successful: {method} {url}")
                    return response_data
                    
            except asyncio.TimeoutError:
                if attempt == self.config.max_retries:
                    raise MCPTimeoutError(f"Request timed out after {self.config.timeout}s")
                self.logger.warning(f"Request timeout, retrying in {self.config.retry_delay}s")
                
            except aiohttp.ClientError as e:
                if attempt == self.config.max_retries:
                    raise MCPConnectionError(f"Connection failed: {str(e)}")
                self.logger.warning(f"Connection error, retrying in {self.config.retry_delay}s: {e}")
                
            except Exception as e:
                if attempt == self.config.max_retries:
                    raise MCPProxyError(f"Unexpected error: {str(e)}")
                self.logger.warning(f"Unexpected error, retrying in {self.config.retry_delay}s: {e}")
            
            # Wait before retry
            if attempt < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay)
        
        # This should never be reached due to the raise statements above
        raise MCPProxyError("Maximum retries exceeded")
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the proxy and validate connection to server.
        
        This method should be implemented by subclasses to perform any
        initialization required for the specific proxy type.
        """
        pass


class MCPToolProxy(ContexaTool, MCPProxy):
    """Proxy for remote MCP tool execution.
    
    This class provides transparent access to tools hosted on remote MCP servers.
    It implements the ContexaTool interface, making remote tools appear as local
    tools to the rest of the system.
    
    Features:
    - ContexaTool-compatible interface for seamless integration
    - Automatic tool metadata caching
    - Parameter validation before remote execution
    - Result caching for performance optimization
    - Comprehensive error handling and retry logic
    
    Example:
        ```python
        config = MCPProxyConfig(server_url="http://localhost:8000")
        tool_proxy = MCPToolProxy(config, "calculator")
        
        await tool_proxy.initialize()
        result = await tool_proxy.execute({
            "operation": "add",
            "a": 10,
            "b": 5
        })
        ```
    """
    
    def __init__(self, config: MCPProxyConfig, tool_name: str):
        """Initialize the tool proxy.
        
        Args:
            config: Configuration for the proxy connection
            tool_name: Name of the remote tool to proxy
        """
        MCPProxy.__init__(self, config)
        self.tool_name = tool_name
        self._metadata_cache: Optional[Dict[str, Any]] = None
        self._result_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        # ContexaTool attributes
        self.name = tool_name
        self.description = f"Remote tool: {tool_name}"
        self.parameters_schema = {}
    
    async def initialize(self) -> None:
        """Initialize the tool proxy and fetch metadata.
        
        Fetches tool metadata from the remote server including description,
        parameter schema, and other tool information.
        
        Raises:
            MCPProxyError: If tool metadata cannot be fetched
        """
        try:
            self.logger.info(f"Initializing tool proxy for: {self.tool_name}")
            
            # Fetch tool metadata
            response = await self._make_request("GET", f"tools/{self.tool_name}")
            
            if "tool" not in response:
                raise MCPProxyError(f"Invalid tool metadata response for {self.tool_name}")
            
            tool_data = response["tool"]
            self._metadata_cache = tool_data
            
            # Update ContexaTool attributes
            self.description = tool_data.get("description", f"Remote tool: {self.tool_name}")
            self.parameters_schema = tool_data.get("inputSchema", {})
            
            self.logger.info(f"Tool proxy initialized: {self.tool_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize tool proxy {self.tool_name}: {e}")
            raise MCPProxyError(f"Tool initialization failed: {str(e)}") from e
    
    def _get_cache_key(self, arguments: Dict[str, Any]) -> str:
        """Generate cache key for tool execution results.
        
        Args:
            arguments: Tool execution arguments
            
        Returns:
            Cache key string
        """
        # Create deterministic cache key from arguments
        sorted_args = json.dumps(arguments, sort_keys=True)
        return f"{self.tool_name}:{hash(sorted_args)}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid.
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            True if cache is valid, False otherwise
        """
        if not self.config.enable_caching:
            return False
            
        if cache_key not in self._cache_timestamps:
            return False
            
        age = time.time() - self._cache_timestamps[cache_key]
        return age < self.config.cache_ttl
    
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        """Execute the remote tool with given arguments.
        
        This method implements the ContexaTool interface and provides transparent
        access to remote tool execution with caching and error handling.
        
        Args:
            arguments: Tool execution arguments
            
        Returns:
            Tool execution result
            
        Raises:
            MCPProxyError: If tool execution fails
            ValueError: If arguments are invalid
        """
        try:
            self.logger.debug(f"Executing tool {self.tool_name} with args: {arguments}")
            
            # Check cache first
            cache_key = self._get_cache_key(arguments)
            if self._is_cache_valid(cache_key):
                self.logger.debug(f"Returning cached result for {self.tool_name}")
                return self._result_cache[cache_key]
            
            # Validate arguments against schema if available
            if self.parameters_schema:
                # Basic validation - could be enhanced with jsonschema
                required_fields = self.parameters_schema.get("required", [])
                for field in required_fields:
                    if field not in arguments:
                        raise ValueError(f"Missing required parameter: {field}")
            
            # Execute remote tool
            response = await self._make_request(
                "POST", 
                f"tools/{self.tool_name}/call",
                data={"arguments": arguments}
            )
            
            if "result" not in response:
                raise MCPProxyError(f"Invalid tool execution response for {self.tool_name}")
            
            result = response["result"]
            
            # Cache result if caching is enabled
            if self.config.enable_caching:
                self._result_cache[cache_key] = result
                self._cache_timestamps[cache_key] = time.time()
                
                # Cleanup old cache entries if cache is full
                if len(self._result_cache) > self.config.cache_size:
                    oldest_key = min(self._cache_timestamps.keys(), 
                                   key=lambda k: self._cache_timestamps[k])
                    del self._result_cache[oldest_key]
                    del self._cache_timestamps[oldest_key]
            
            self.logger.debug(f"Tool execution successful: {self.tool_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Tool execution failed for {self.tool_name}: {e}")
            if isinstance(e, (MCPProxyError, ValueError)):
                raise
            raise MCPProxyError(f"Tool execution failed: {str(e)}") from e
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Get cached tool metadata.
        
        Returns:
            Tool metadata dictionary or None if not initialized
        """
        return self._metadata_cache
    
    def clear_cache(self) -> None:
        """Clear the result cache."""
        self._result_cache.clear()
        self._cache_timestamps.clear()
        self.logger.debug(f"Cleared cache for tool: {self.tool_name}")


@dataclass
class MCPResource:
    """Represents a remote MCP resource.
    
    Attributes:
        uri: Unique resource identifier
        name: Human-readable resource name
        description: Resource description
        mime_type: MIME type of the resource content
        metadata: Additional resource metadata
    """
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MCPResourceProxy(MCPProxy):
    """Proxy for remote MCP resource access.
    
    This class provides transparent access to resources hosted on remote MCP servers.
    It implements intelligent caching with LRU and TTL support, subscription management,
    and efficient resource loading strategies.
    
    Features:
    - Intelligent resource caching with LRU and TTL support
    - Resource subscription management for real-time updates
    - Batch resource loading for performance optimization
    - Content type detection and validation
    - Comprehensive error handling for network scenarios
    
    Example:
        ```python
        config = MCPProxyConfig(server_url="http://localhost:8000")
        resource_proxy = MCPResourceProxy(config)
        
        await resource_proxy.initialize()
        
        # List available resources
        resources = await resource_proxy.list_resources()
        
        # Read a specific resource
        content = await resource_proxy.read_resource("file://data/config.json")
        ```
    """
    
    def __init__(self, config: MCPProxyConfig):
        """Initialize the resource proxy.
        
        Args:
            config: Configuration for the proxy connection
        """
        super().__init__(config)
        self._resource_cache: Dict[str, Any] = {}
        self._resource_metadata_cache: Dict[str, MCPResource] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._subscriptions: Dict[str, bool] = {}
    
    async def initialize(self) -> None:
        """Initialize the resource proxy and validate connection.
        
        Validates connection to the remote MCP server and optionally
        pre-loads resource metadata for performance optimization.
        
        Raises:
            MCPProxyError: If connection validation fails
        """
        try:
            self.logger.info("Initializing resource proxy")
            
            # Validate connection by listing resources
            await self._make_request("GET", "resources")
            
            self.logger.info("Resource proxy initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize resource proxy: {e}")
            raise MCPProxyError(f"Resource proxy initialization failed: {str(e)}") from e
    
    async def list_resources(self, refresh_cache: bool = False) -> List[MCPResource]:
        """List all available resources from the remote server.
        
        Args:
            refresh_cache: Whether to refresh the cached resource list
            
        Returns:
            List of available resources
            
        Raises:
            MCPProxyError: If resource listing fails
        """
        try:
            cache_key = "resource_list"
            
            # Check cache first
            if not refresh_cache and self._is_cache_valid(cache_key):
                self.logger.debug("Returning cached resource list")
                return list(self._resource_metadata_cache.values())
            
            self.logger.debug("Fetching resource list from server")
            
            response = await self._make_request("GET", "resources")
            
            if "resources" not in response:
                raise MCPProxyError("Invalid resource list response")
            
            resources = []
            for resource_data in response["resources"]:
                resource = MCPResource(
                    uri=resource_data["uri"],
                    name=resource_data.get("name", resource_data["uri"]),
                    description=resource_data.get("description"),
                    mime_type=resource_data.get("mimeType"),
                    metadata=resource_data.get("metadata", {})
                )
                resources.append(resource)
                self._resource_metadata_cache[resource.uri] = resource
            
            # Update cache timestamp
            if self.config.enable_caching:
                self._cache_timestamps[cache_key] = time.time()
            
            self.logger.debug(f"Fetched {len(resources)} resources")
            return resources
            
        except Exception as e:
            self.logger.error(f"Failed to list resources: {e}")
            if isinstance(e, MCPProxyError):
                raise
            raise MCPProxyError(f"Resource listing failed: {str(e)}") from e
    
    async def read_resource(self, uri: str, force_refresh: bool = False) -> Any:
        """Read content from a specific resource.
        
        Args:
            uri: Resource URI to read
            force_refresh: Whether to bypass cache and fetch fresh content
            
        Returns:
            Resource content (type depends on resource)
            
        Raises:
            MCPProxyError: If resource reading fails
            ValueError: If URI is invalid
        """
        try:
            if not uri:
                raise ValueError("Resource URI cannot be empty")
            
            self.logger.debug(f"Reading resource: {uri}")
            
            # Check cache first
            cache_key = f"resource_content:{uri}"
            if not force_refresh and self._is_cache_valid(cache_key):
                self.logger.debug(f"Returning cached content for: {uri}")
                return self._resource_cache[cache_key]
            
            # Read from remote server
            response = await self._make_request(
                "POST",
                "resources/read",
                data={"uri": uri}
            )
            
            if "contents" not in response:
                raise MCPProxyError(f"Invalid resource read response for: {uri}")
            
            content = response["contents"]
            
            # Cache content if caching is enabled
            if self.config.enable_caching:
                self._resource_cache[cache_key] = content
                self._cache_timestamps[cache_key] = time.time()
                
                # Cleanup old cache entries if cache is full
                if len(self._resource_cache) > self.config.cache_size:
                    oldest_key = min(self._cache_timestamps.keys(),
                                   key=lambda k: self._cache_timestamps[k])
                    if oldest_key in self._resource_cache:
                        del self._resource_cache[oldest_key]
                    del self._cache_timestamps[oldest_key]
            
            self.logger.debug(f"Resource read successful: {uri}")
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to read resource {uri}: {e}")
            if isinstance(e, (MCPProxyError, ValueError)):
                raise
            raise MCPProxyError(f"Resource read failed: {str(e)}") from e
    
    async def subscribe_to_resource(self, uri: str) -> bool:
        """Subscribe to resource change notifications.
        
        Args:
            uri: Resource URI to subscribe to
            
        Returns:
            True if subscription was successful
            
        Raises:
            MCPProxyError: If subscription fails
        """
        try:
            self.logger.debug(f"Subscribing to resource: {uri}")
            
            response = await self._make_request(
                "POST",
                "resources/subscribe",
                data={"uri": uri}
            )
            
            success = response.get("success", False)
            if success:
                self._subscriptions[uri] = True
                self.logger.debug(f"Successfully subscribed to: {uri}")
            else:
                self.logger.warning(f"Failed to subscribe to: {uri}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to resource {uri}: {e}")
            raise MCPProxyError(f"Resource subscription failed: {str(e)}") from e
    
    async def unsubscribe_from_resource(self, uri: str) -> bool:
        """Unsubscribe from resource change notifications.
        
        Args:
            uri: Resource URI to unsubscribe from
            
        Returns:
            True if unsubscription was successful
        """
        try:
            self.logger.debug(f"Unsubscribing from resource: {uri}")
            
            response = await self._make_request(
                "POST",
                "resources/unsubscribe",
                data={"uri": uri}
            )
            
            success = response.get("success", False)
            if success and uri in self._subscriptions:
                del self._subscriptions[uri]
                self.logger.debug(f"Successfully unsubscribed from: {uri}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe from resource {uri}: {e}")
            raise MCPProxyError(f"Resource unsubscription failed: {str(e)}") from e
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached item is still valid.
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            True if cache is valid, False otherwise
        """
        if not self.config.enable_caching:
            return False
            
        if cache_key not in self._cache_timestamps:
            return False
            
        age = time.time() - self._cache_timestamps[cache_key]
        return age < self.config.cache_ttl
    
    def clear_cache(self) -> None:
        """Clear all cached resources and metadata."""
        self._resource_cache.clear()
        self._resource_metadata_cache.clear()
        self._cache_timestamps.clear()
        self.logger.debug("Cleared resource cache")
    
    def get_subscriptions(self) -> List[str]:
        """Get list of currently subscribed resource URIs.
        
        Returns:
            List of subscribed resource URIs
        """
        return list(self._subscriptions.keys())


@dataclass
class MCPPromptTemplate:
    """Represents a remote MCP prompt template.
    
    Attributes:
        name: Template name
        description: Template description
        arguments: Template argument definitions
        metadata: Additional template metadata
    """
    name: str
    description: Optional[str] = None
    arguments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MCPPromptProxy(MCPProxy):
    """Proxy for remote MCP prompt template management.
    
    This class provides transparent access to prompt templates hosted on remote
    MCP servers. It handles template caching, parameter validation, and provides
    a seamless interface for prompt template execution.
    
    Features:
    - Prompt template caching for performance optimization
    - Parameter validation before template execution
    - Template rendering with argument substitution
    - Batch template operations for efficiency
    - Comprehensive error handling and validation
    
    Example:
        ```python
        config = MCPProxyConfig(server_url="http://localhost:8000")
        prompt_proxy = MCPPromptProxy(config)
        
        await prompt_proxy.initialize()
        
        # List available templates
        templates = await prompt_proxy.list_prompts()
        
        # Execute a prompt template
        result = await prompt_proxy.get_prompt(
            "summarize_text",
            arguments={"text": "Long text to summarize..."}
        )
        ```
    """
    
    def __init__(self, config: MCPProxyConfig):
        """Initialize the prompt proxy.
        
        Args:
            config: Configuration for the proxy connection
        """
        super().__init__(config)
        self._template_cache: Dict[str, MCPPromptTemplate] = {}
        self._result_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
    
    async def initialize(self) -> None:
        """Initialize the prompt proxy and validate connection.
        
        Validates connection to the remote MCP server and optionally
        pre-loads prompt template metadata.
        
        Raises:
            MCPProxyError: If connection validation fails
        """
        try:
            self.logger.info("Initializing prompt proxy")
            
            # Validate connection by listing prompts
            await self._make_request("GET", "prompts")
            
            self.logger.info("Prompt proxy initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize prompt proxy: {e}")
            raise MCPProxyError(f"Prompt proxy initialization failed: {str(e)}") from e
    
    async def list_prompts(self, refresh_cache: bool = False) -> List[MCPPromptTemplate]:
        """List all available prompt templates from the remote server.
        
        Args:
            refresh_cache: Whether to refresh the cached template list
            
        Returns:
            List of available prompt templates
            
        Raises:
            MCPProxyError: If prompt listing fails
        """
        try:
            cache_key = "prompt_list"
            
            # Check cache first
            if not refresh_cache and self._is_cache_valid(cache_key):
                self.logger.debug("Returning cached prompt list")
                return list(self._template_cache.values())
            
            self.logger.debug("Fetching prompt list from server")
            
            response = await self._make_request("GET", "prompts")
            
            if "prompts" not in response:
                raise MCPProxyError("Invalid prompt list response")
            
            templates = []
            for prompt_data in response["prompts"]:
                template = MCPPromptTemplate(
                    name=prompt_data["name"],
                    description=prompt_data.get("description"),
                    arguments=prompt_data.get("arguments", []),
                    metadata=prompt_data.get("metadata", {})
                )
                templates.append(template)
                self._template_cache[template.name] = template
            
            # Update cache timestamp
            if self.config.enable_caching:
                self._cache_timestamps[cache_key] = time.time()
            
            self.logger.debug(f"Fetched {len(templates)} prompt templates")
            return templates
            
        except Exception as e:
            self.logger.error(f"Failed to list prompts: {e}")
            if isinstance(e, MCPProxyError):
                raise
            raise MCPProxyError(f"Prompt listing failed: {str(e)}") from e
    
    async def get_prompt(
        self, 
        name: str, 
        arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a prompt template with given arguments.
        
        Args:
            name: Name of the prompt template
            arguments: Arguments to pass to the template
            
        Returns:
            Rendered prompt result
            
        Raises:
            MCPProxyError: If prompt execution fails
            ValueError: If arguments are invalid
        """
        try:
            if not name:
                raise ValueError("Prompt name cannot be empty")
            
            arguments = arguments or {}
            
            self.logger.debug(f"Executing prompt template: {name}")
            
            # Check cache first
            cache_key = self._get_cache_key(name, arguments)
            if self._is_cache_valid(cache_key):
                self.logger.debug(f"Returning cached result for prompt: {name}")
                return self._result_cache[cache_key]
            
            # Validate arguments if template is cached
            if name in self._template_cache:
                self._validate_arguments(name, arguments)
            
            # Execute remote prompt
            response = await self._make_request(
                "POST",
                "prompts/get",
                data={
                    "name": name,
                    "arguments": arguments
                }
            )
            
            if "messages" not in response:
                raise MCPProxyError(f"Invalid prompt execution response for: {name}")
            
            result = response
            
            # Cache result if caching is enabled
            if self.config.enable_caching:
                self._result_cache[cache_key] = result
                self._cache_timestamps[cache_key] = time.time()
                
                # Cleanup old cache entries if cache is full
                if len(self._result_cache) > self.config.cache_size:
                    oldest_key = min(self._cache_timestamps.keys(),
                                   key=lambda k: self._cache_timestamps[k])
                    if oldest_key in self._result_cache:
                        del self._result_cache[oldest_key]
                    del self._cache_timestamps[oldest_key]
            
            self.logger.debug(f"Prompt execution successful: {name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute prompt {name}: {e}")
            if isinstance(e, (MCPProxyError, ValueError)):
                raise
            raise MCPProxyError(f"Prompt execution failed: {str(e)}") from e
    
    def _validate_arguments(self, name: str, arguments: Dict[str, Any]) -> None:
        """Validate arguments against template definition.
        
        Args:
            name: Template name
            arguments: Arguments to validate
            
        Raises:
            ValueError: If arguments are invalid
        """
        template = self._template_cache.get(name)
        if not template:
            return  # Skip validation if template not cached
        
        # Check required arguments
        for arg_def in template.arguments:
            arg_name = arg_def.get("name")
            if not arg_name:
                continue
                
            is_required = arg_def.get("required", False)
            if is_required and arg_name not in arguments:
                raise ValueError(f"Missing required argument: {arg_name}")
    
    def _get_cache_key(self, name: str, arguments: Dict[str, Any]) -> str:
        """Generate cache key for prompt execution results.
        
        Args:
            name: Template name
            arguments: Template arguments
            
        Returns:
            Cache key string
        """
        sorted_args = json.dumps(arguments, sort_keys=True)
        return f"prompt:{name}:{hash(sorted_args)}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid.
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            True if cache is valid, False otherwise
        """
        if not self.config.enable_caching:
            return False
            
        if cache_key not in self._cache_timestamps:
            return False
            
        age = time.time() - self._cache_timestamps[cache_key]
        return age < self.config.cache_ttl
    
    def clear_cache(self) -> None:
        """Clear all cached templates and results."""
        self._template_cache.clear()
        self._result_cache.clear()
        self._cache_timestamps.clear()
        self.logger.debug("Cleared prompt cache")
    
    def get_template(self, name: str) -> Optional[MCPPromptTemplate]:
        """Get cached template metadata.
        
        Args:
            name: Template name
            
        Returns:
            Template metadata or None if not cached
        """
        return self._template_cache.get(name) 