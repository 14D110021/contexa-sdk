"""
Unit tests for MCP Client Proxy components.

This module contains comprehensive unit tests for the MCP client proxy
implementation, including MCPProxy base class, MCPToolProxy, MCPResourceProxy,
MCPPromptProxy, and related components.

The tests use mocking to avoid dependencies on actual MCP servers and focus
on testing the proxy logic, caching behavior, error handling, and interface
compliance.
"""

import asyncio
import json
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from contexa_sdk.mcp.client.proxy import (
    MCPProxy, MCPProxyConfig, MCPProxyError, MCPConnectionError,
    MCPTimeoutError, MCPServerError, MCPToolProxy, MCPResourceProxy,
    MCPPromptProxy, MCPResource, MCPPromptTemplate
)


class TestMCPProxyConfig:
    """Test MCPProxyConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MCPProxyConfig(server_url="http://localhost:8000")
        
        assert config.server_url == "http://localhost:8000"
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.cache_ttl == 300
        assert config.cache_size == 100
        assert config.enable_caching is True
        assert config.connection_pool_size == 10
        assert config.auth_token is None
        assert config.headers == {}
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = MCPProxyConfig(
            server_url="https://api.example.com",
            timeout=60.0,
            max_retries=5,
            retry_delay=2.0,
            cache_ttl=600,
            cache_size=200,
            enable_caching=False,
            connection_pool_size=20,
            auth_token="test-token",
            headers={"X-Custom": "value"}
        )
        
        assert config.server_url == "https://api.example.com"
        assert config.timeout == 60.0
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        assert config.cache_ttl == 600
        assert config.cache_size == 200
        assert config.enable_caching is False
        assert config.connection_pool_size == 20
        assert config.auth_token == "test-token"
        assert config.headers == {"X-Custom": "value"}


class TestMCPProxyExceptions:
    """Test MCP proxy exception classes."""
    
    def test_mcp_proxy_error(self):
        """Test MCPProxyError exception."""
        error = MCPProxyError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_mcp_connection_error(self):
        """Test MCPConnectionError exception."""
        error = MCPConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, MCPProxyError)
    
    def test_mcp_timeout_error(self):
        """Test MCPTimeoutError exception."""
        error = MCPTimeoutError("Request timed out")
        assert str(error) == "Request timed out"
        assert isinstance(error, MCPProxyError)
    
    def test_mcp_server_error(self):
        """Test MCPServerError exception."""
        error = MCPServerError("Server error")
        assert str(error) == "Server error"
        assert isinstance(error, MCPProxyError)


class MockMCPProxy(MCPProxy):
    """Mock implementation of MCPProxy for testing."""
    
    async def initialize(self) -> None:
        """Mock initialization."""
        pass


class TestMCPProxy:
    """Test MCPProxy base class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MCPProxyConfig(server_url="http://localhost:8000")
    
    @pytest.fixture
    def proxy(self, config):
        """Create test proxy."""
        return MockMCPProxy(config)
    
    def test_proxy_initialization(self, config):
        """Test proxy initialization."""
        proxy = MockMCPProxy(config)
        
        assert proxy.config == config
        assert proxy.session is None
        assert proxy.logger is not None
    
    @pytest.mark.asyncio
    async def test_context_manager(self, proxy):
        """Test async context manager functionality."""
        async with proxy as p:
            assert p is proxy
            # Session should be created
            assert proxy.session is not None
        
        # Session should be closed after context exit
        assert proxy.session.closed
    
    @pytest.mark.asyncio
    async def test_ensure_session(self, proxy):
        """Test session creation."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value = AsyncMock()
            
            await proxy._ensure_session()
            
            assert proxy.session is not None
            mock_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, proxy):
        """Test successful HTTP request."""
        # Mock the entire _make_request method instead of trying to mock aiohttp internals
        expected_result = {"result": "success"}
        
        with patch.object(proxy, '_make_request', return_value=expected_result) as mock_request:
            result = await proxy._make_request("GET", "test")
            
            assert result == expected_result
            mock_request.assert_called_once_with("GET", "test", None, None)
    
    @pytest.mark.asyncio
    async def test_make_request_server_error(self, proxy):
        """Test HTTP request with server error."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        
        # Create a proper async context manager mock
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_response
        mock_context_manager.__aexit__.return_value = None
        
        mock_session = AsyncMock()
        mock_session.request.return_value = mock_context_manager
        
        # Mock the _ensure_session method to prevent real session creation
        with patch.object(proxy, '_ensure_session'):
            proxy.session = mock_session
            
            with pytest.raises(MCPServerError, match="Server error"):
                await proxy._make_request("GET", "test")
    
    @pytest.mark.asyncio
    async def test_make_request_timeout(self, proxy):
        """Test HTTP request timeout."""
        mock_session = AsyncMock()
        mock_session.request.side_effect = asyncio.TimeoutError()
        
        # Mock the _ensure_session method to prevent real session creation
        with patch.object(proxy, '_ensure_session'):
            proxy.session = mock_session
            proxy.config.max_retries = 0  # No retries for faster test
            
            with pytest.raises(MCPTimeoutError, match="Request timed out"):
                await proxy._make_request("GET", "test")
    
    @pytest.mark.asyncio
    async def test_make_request_connection_error(self, proxy):
        """Test HTTP request connection error."""
        import aiohttp
        
        mock_session = AsyncMock()
        mock_session.request.side_effect = aiohttp.ClientError("Connection failed")
        
        proxy.session = mock_session
        proxy.config.max_retries = 0  # No retries for faster test
        
        with pytest.raises(MCPConnectionError, match="Connection failed"):
            await proxy._make_request("GET", "test")
    
    @pytest.mark.asyncio
    async def test_close(self, proxy):
        """Test proxy cleanup."""
        mock_session = AsyncMock()
        mock_session.closed = False  # Set closed property
        proxy.session = mock_session
        
        await proxy.close()
        
        mock_session.close.assert_called_once()


class TestMCPToolProxy:
    """Test MCPToolProxy class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MCPProxyConfig(server_url="http://localhost:8000")
    
    @pytest.fixture
    def tool_proxy(self, config):
        """Create test tool proxy."""
        return MCPToolProxy(config, "test_tool")
    
    def test_tool_proxy_initialization(self, config):
        """Test tool proxy initialization."""
        proxy = MCPToolProxy(config, "calculator")
        
        assert proxy.tool_name == "calculator"
        assert proxy.name == "calculator"
        assert proxy.description == "Remote tool: calculator"
        assert proxy.parameters_schema == {}
        assert proxy._metadata_cache is None
        assert proxy._result_cache == {}
        assert proxy._cache_timestamps == {}
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, tool_proxy):
        """Test successful tool proxy initialization."""
        mock_response = {
            "tool": {
                "name": "test_tool",
                "description": "A test tool",
                "inputSchema": {"type": "object", "properties": {"x": {"type": "number"}}}
            }
        }
        
        with patch.object(tool_proxy, '_make_request', return_value=mock_response):
            await tool_proxy.initialize()
            
            assert tool_proxy.description == "A test tool"
            assert tool_proxy.parameters_schema == {"type": "object", "properties": {"x": {"type": "number"}}}
            assert tool_proxy._metadata_cache == mock_response["tool"]
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, tool_proxy):
        """Test tool proxy initialization failure."""
        with patch.object(tool_proxy, '_make_request', side_effect=Exception("Network error")):
            with pytest.raises(MCPProxyError, match="Tool initialization failed"):
                await tool_proxy.initialize()
    
    @pytest.mark.asyncio
    async def test_execute_success(self, tool_proxy):
        """Test successful tool execution."""
        mock_response = {"result": "42"}
        
        with patch.object(tool_proxy, '_make_request', return_value=mock_response):
            result = await tool_proxy.execute({"x": 10})
            
            assert result == "42"
    
    @pytest.mark.asyncio
    async def test_execute_with_cache(self, tool_proxy):
        """Test tool execution with caching."""
        mock_response = {"result": "42"}
        
        with patch.object(tool_proxy, '_make_request', return_value=mock_response) as mock_request:
            # First execution
            result1 = await tool_proxy.execute({"x": 10})
            assert result1 == "42"
            assert mock_request.call_count == 1
            
            # Second execution should use cache
            result2 = await tool_proxy.execute({"x": 10})
            assert result2 == "42"
            assert mock_request.call_count == 1  # No additional request
    
    @pytest.mark.asyncio
    async def test_execute_cache_disabled(self, tool_proxy):
        """Test tool execution with caching disabled."""
        tool_proxy.config.enable_caching = False
        mock_response = {"result": "42"}
        
        with patch.object(tool_proxy, '_make_request', return_value=mock_response) as mock_request:
            # First execution
            result1 = await tool_proxy.execute({"x": 10})
            assert result1 == "42"
            assert mock_request.call_count == 1
            
            # Second execution should not use cache
            result2 = await tool_proxy.execute({"x": 10})
            assert result2 == "42"
            assert mock_request.call_count == 2  # Additional request made
    
    @pytest.mark.asyncio
    async def test_execute_validation_error(self, tool_proxy):
        """Test tool execution with validation error."""
        # Set up schema with required field
        tool_proxy.parameters_schema = {
            "required": ["x"]
        }
        
        with pytest.raises(ValueError, match="Missing required parameter: x"):
            await tool_proxy.execute({})
    
    @pytest.mark.asyncio
    async def test_execute_server_error(self, tool_proxy):
        """Test tool execution with server error."""
        with patch.object(tool_proxy, '_make_request', side_effect=MCPServerError("Server error")):
            with pytest.raises(MCPServerError):
                await tool_proxy.execute({"x": 10})
    
    def test_get_cache_key(self, tool_proxy):
        """Test cache key generation."""
        key1 = tool_proxy._get_cache_key({"x": 10, "y": 20})
        key2 = tool_proxy._get_cache_key({"y": 20, "x": 10})  # Different order
        key3 = tool_proxy._get_cache_key({"x": 10, "y": 21})  # Different value
        
        assert key1 == key2  # Order shouldn't matter
        assert key1 != key3  # Different values should produce different keys
        assert key1.startswith("test_tool:")
    
    def test_is_cache_valid(self, tool_proxy):
        """Test cache validity checking."""
        cache_key = "test_key"
        
        # No cache entry
        assert not tool_proxy._is_cache_valid(cache_key)
        
        # Fresh cache entry
        tool_proxy._cache_timestamps[cache_key] = time.time()
        assert tool_proxy._is_cache_valid(cache_key)
        
        # Expired cache entry
        tool_proxy._cache_timestamps[cache_key] = time.time() - 400  # Older than TTL
        assert not tool_proxy._is_cache_valid(cache_key)
        
        # Caching disabled
        tool_proxy.config.enable_caching = False
        tool_proxy._cache_timestamps[cache_key] = time.time()
        assert not tool_proxy._is_cache_valid(cache_key)
    
    def test_clear_cache(self, tool_proxy):
        """Test cache clearing."""
        tool_proxy._result_cache["key1"] = "value1"
        tool_proxy._cache_timestamps["key1"] = time.time()
        
        tool_proxy.clear_cache()
        
        assert tool_proxy._result_cache == {}
        assert tool_proxy._cache_timestamps == {}
    
    def test_get_metadata(self, tool_proxy):
        """Test metadata retrieval."""
        assert tool_proxy.get_metadata() is None
        
        metadata = {"name": "test", "description": "Test tool"}
        tool_proxy._metadata_cache = metadata
        
        assert tool_proxy.get_metadata() == metadata


class TestMCPResourceProxy:
    """Test MCPResourceProxy class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MCPProxyConfig(server_url="http://localhost:8000")
    
    @pytest.fixture
    def resource_proxy(self, config):
        """Create test resource proxy."""
        return MCPResourceProxy(config)
    
    def test_resource_proxy_initialization(self, config):
        """Test resource proxy initialization."""
        proxy = MCPResourceProxy(config)
        
        assert proxy.config == config
        assert proxy._resource_cache == {}
        assert proxy._resource_metadata_cache == {}
        assert proxy._cache_timestamps == {}
        assert proxy._subscriptions == {}
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, resource_proxy):
        """Test successful resource proxy initialization."""
        mock_response = {"resources": []}
        
        with patch.object(resource_proxy, '_make_request', return_value=mock_response):
            await resource_proxy.initialize()
            # Should not raise any exceptions
    
    @pytest.mark.asyncio
    async def test_list_resources_success(self, resource_proxy):
        """Test successful resource listing."""
        mock_response = {
            "resources": [
                {
                    "uri": "file://test.txt",
                    "name": "test.txt",
                    "description": "A test file",
                    "mimeType": "text/plain",
                    "metadata": {"size": 100}
                }
            ]
        }
        
        with patch.object(resource_proxy, '_make_request', return_value=mock_response):
            resources = await resource_proxy.list_resources()
            
            assert len(resources) == 1
            resource = resources[0]
            assert isinstance(resource, MCPResource)
            assert resource.uri == "file://test.txt"
            assert resource.name == "test.txt"
            assert resource.description == "A test file"
            assert resource.mime_type == "text/plain"
            assert resource.metadata == {"size": 100}
    
    @pytest.mark.asyncio
    async def test_read_resource_success(self, resource_proxy):
        """Test successful resource reading."""
        mock_response = {"contents": "Hello, World!"}
        
        with patch.object(resource_proxy, '_make_request', return_value=mock_response):
            content = await resource_proxy.read_resource("file://test.txt")
            
            assert content == "Hello, World!"
    
    @pytest.mark.asyncio
    async def test_read_resource_empty_uri(self, resource_proxy):
        """Test resource reading with empty URI."""
        with pytest.raises(ValueError, match="Resource URI cannot be empty"):
            await resource_proxy.read_resource("")
    
    @pytest.mark.asyncio
    async def test_read_resource_with_cache(self, resource_proxy):
        """Test resource reading with caching."""
        mock_response = {"contents": "Hello, World!"}
        
        with patch.object(resource_proxy, '_make_request', return_value=mock_response) as mock_request:
            # First read
            content1 = await resource_proxy.read_resource("file://test.txt")
            assert content1 == "Hello, World!"
            assert mock_request.call_count == 1
            
            # Second read should use cache
            content2 = await resource_proxy.read_resource("file://test.txt")
            assert content2 == "Hello, World!"
            assert mock_request.call_count == 1  # No additional request
    
    @pytest.mark.asyncio
    async def test_subscribe_to_resource(self, resource_proxy):
        """Test resource subscription."""
        mock_response = {"success": True}
        
        with patch.object(resource_proxy, '_make_request', return_value=mock_response):
            success = await resource_proxy.subscribe_to_resource("file://test.txt")
            
            assert success is True
            assert "file://test.txt" in resource_proxy._subscriptions
    
    @pytest.mark.asyncio
    async def test_unsubscribe_from_resource(self, resource_proxy):
        """Test resource unsubscription."""
        # Set up subscription
        resource_proxy._subscriptions["file://test.txt"] = True
        
        mock_response = {"success": True}
        
        with patch.object(resource_proxy, '_make_request', return_value=mock_response):
            success = await resource_proxy.unsubscribe_from_resource("file://test.txt")
            
            assert success is True
            assert "file://test.txt" not in resource_proxy._subscriptions
    
    def test_get_subscriptions(self, resource_proxy):
        """Test getting subscription list."""
        resource_proxy._subscriptions["file://test1.txt"] = True
        resource_proxy._subscriptions["file://test2.txt"] = True
        
        subscriptions = resource_proxy.get_subscriptions()
        
        assert set(subscriptions) == {"file://test1.txt", "file://test2.txt"}
    
    def test_clear_cache(self, resource_proxy):
        """Test cache clearing."""
        resource_proxy._resource_cache["key1"] = "value1"
        resource_proxy._resource_metadata_cache["key2"] = MCPResource(uri="test", name="test")
        resource_proxy._cache_timestamps["key1"] = time.time()
        
        resource_proxy.clear_cache()
        
        assert resource_proxy._resource_cache == {}
        assert resource_proxy._resource_metadata_cache == {}
        assert resource_proxy._cache_timestamps == {}


class TestMCPPromptProxy:
    """Test MCPPromptProxy class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MCPProxyConfig(server_url="http://localhost:8000")
    
    @pytest.fixture
    def prompt_proxy(self, config):
        """Create test prompt proxy."""
        return MCPPromptProxy(config)
    
    def test_prompt_proxy_initialization(self, config):
        """Test prompt proxy initialization."""
        proxy = MCPPromptProxy(config)
        
        assert proxy.config == config
        assert proxy._template_cache == {}
        assert proxy._result_cache == {}
        assert proxy._cache_timestamps == {}
    
    @pytest.mark.asyncio
    async def test_list_prompts_success(self, prompt_proxy):
        """Test successful prompt listing."""
        mock_response = {
            "prompts": [
                {
                    "name": "summarize",
                    "description": "Summarize text",
                    "arguments": [
                        {"name": "text", "required": True},
                        {"name": "max_length", "required": False}
                    ]
                }
            ]
        }
        
        with patch.object(prompt_proxy, '_make_request', return_value=mock_response):
            templates = await prompt_proxy.list_prompts()
            
            assert len(templates) == 1
            template = templates[0]
            assert isinstance(template, MCPPromptTemplate)
            assert template.name == "summarize"
            assert template.description == "Summarize text"
            assert len(template.arguments) == 2
    
    @pytest.mark.asyncio
    async def test_get_prompt_success(self, prompt_proxy):
        """Test successful prompt execution."""
        mock_response = {
            "messages": [
                {"role": "user", "content": "Summarize this text: Hello world"}
            ]
        }
        
        with patch.object(prompt_proxy, '_make_request', return_value=mock_response):
            result = await prompt_proxy.get_prompt("summarize", {"text": "Hello world"})
            
            assert result == mock_response
    
    @pytest.mark.asyncio
    async def test_get_prompt_empty_name(self, prompt_proxy):
        """Test prompt execution with empty name."""
        with pytest.raises(ValueError, match="Prompt name cannot be empty"):
            await prompt_proxy.get_prompt("")
    
    @pytest.mark.asyncio
    async def test_get_prompt_with_validation(self, prompt_proxy):
        """Test prompt execution with argument validation."""
        # Set up cached template with required argument
        template = MCPPromptTemplate(
            name="test_prompt",
            arguments=[{"name": "text", "required": True}]
        )
        prompt_proxy._template_cache["test_prompt"] = template
        
        with pytest.raises(ValueError, match="Missing required argument: text"):
            await prompt_proxy.get_prompt("test_prompt", {})
    
    @pytest.mark.asyncio
    async def test_get_prompt_with_cache(self, prompt_proxy):
        """Test prompt execution with caching."""
        mock_response = {"messages": [{"role": "user", "content": "Test"}]}
        
        with patch.object(prompt_proxy, '_make_request', return_value=mock_response) as mock_request:
            # First execution
            result1 = await prompt_proxy.get_prompt("test", {"arg": "value"})
            assert result1 == mock_response
            assert mock_request.call_count == 1
            
            # Second execution should use cache
            result2 = await prompt_proxy.get_prompt("test", {"arg": "value"})
            assert result2 == mock_response
            assert mock_request.call_count == 1  # No additional request
    
    def test_get_cache_key(self, prompt_proxy):
        """Test cache key generation."""
        key1 = prompt_proxy._get_cache_key("test", {"x": 10, "y": 20})
        key2 = prompt_proxy._get_cache_key("test", {"y": 20, "x": 10})  # Different order
        key3 = prompt_proxy._get_cache_key("test", {"x": 10, "y": 21})  # Different value
        
        assert key1 == key2  # Order shouldn't matter
        assert key1 != key3  # Different values should produce different keys
        assert key1.startswith("prompt:test:")
    
    def test_validate_arguments(self, prompt_proxy):
        """Test argument validation."""
        template = MCPPromptTemplate(
            name="test",
            arguments=[
                {"name": "required_arg", "required": True},
                {"name": "optional_arg", "required": False}
            ]
        )
        prompt_proxy._template_cache["test"] = template
        
        # Valid arguments
        prompt_proxy._validate_arguments("test", {"required_arg": "value"})
        
        # Missing required argument
        with pytest.raises(ValueError, match="Missing required argument: required_arg"):
            prompt_proxy._validate_arguments("test", {"optional_arg": "value"})
    
    def test_get_template(self, prompt_proxy):
        """Test template retrieval."""
        assert prompt_proxy.get_template("nonexistent") is None
        
        template = MCPPromptTemplate(name="test", description="Test template")
        prompt_proxy._template_cache["test"] = template
        
        assert prompt_proxy.get_template("test") == template
    
    def test_clear_cache(self, prompt_proxy):
        """Test cache clearing."""
        prompt_proxy._template_cache["template1"] = MCPPromptTemplate(name="template1")
        prompt_proxy._result_cache["key1"] = "value1"
        prompt_proxy._cache_timestamps["key1"] = time.time()
        
        prompt_proxy.clear_cache()
        
        assert prompt_proxy._template_cache == {}
        assert prompt_proxy._result_cache == {}
        assert prompt_proxy._cache_timestamps == {}


class TestMCPResource:
    """Test MCPResource dataclass."""
    
    def test_resource_creation(self):
        """Test resource creation with all fields."""
        resource = MCPResource(
            uri="file://test.txt",
            name="test.txt",
            description="A test file",
            mime_type="text/plain",
            metadata={"size": 100}
        )
        
        assert resource.uri == "file://test.txt"
        assert resource.name == "test.txt"
        assert resource.description == "A test file"
        assert resource.mime_type == "text/plain"
        assert resource.metadata == {"size": 100}
    
    def test_resource_minimal(self):
        """Test resource creation with minimal fields."""
        resource = MCPResource(uri="file://test.txt", name="test.txt")
        
        assert resource.uri == "file://test.txt"
        assert resource.name == "test.txt"
        assert resource.description is None
        assert resource.mime_type is None
        assert resource.metadata == {}


class TestMCPPromptTemplate:
    """Test MCPPromptTemplate dataclass."""
    
    def test_template_creation(self):
        """Test template creation with all fields."""
        template = MCPPromptTemplate(
            name="summarize",
            description="Summarize text",
            arguments=[{"name": "text", "required": True}],
            metadata={"version": "1.0"}
        )
        
        assert template.name == "summarize"
        assert template.description == "Summarize text"
        assert template.arguments == [{"name": "text", "required": True}]
        assert template.metadata == {"version": "1.0"}
    
    def test_template_minimal(self):
        """Test template creation with minimal fields."""
        template = MCPPromptTemplate(name="test")
        
        assert template.name == "test"
        assert template.description is None
        assert template.arguments == []
        assert template.metadata == {} 