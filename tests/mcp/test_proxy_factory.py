"""
Unit tests for MCP Proxy Factory components.

This module contains comprehensive unit tests for the MCP proxy factory
implementation, including MCPProxyFactory, MCPProxyManager, and related
utility functions.

The tests use mocking to avoid dependencies on actual MCP servers and focus
on testing the factory logic, proxy management, lifecycle handling, and
error scenarios.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from contexa_sdk.mcp.client.proxy import MCPProxyConfig, MCPProxyError
from contexa_sdk.mcp.client.proxy_factory import (
    MCPProxyFactory, MCPProxyManager, create_mcp_proxy_factory
)


class TestMCPProxyFactory:
    """Test MCPProxyFactory class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MCPProxyConfig(server_url="http://localhost:8000")
    
    @pytest.fixture
    def factory(self, config):
        """Create test proxy factory."""
        return MCPProxyFactory(config)
    
    def test_factory_initialization(self, config):
        """Test factory initialization."""
        factory = MCPProxyFactory(config)
        
        assert factory.config == config
        assert factory.proxies == {}
        assert factory.logger is not None
        assert not factory._closed
    
    @pytest.mark.asyncio
    async def test_context_manager(self, factory):
        """Test async context manager functionality."""
        async with factory as f:
            assert f is factory
            assert not factory.is_closed()
        
        # Factory should be closed after context exit
        assert factory.is_closed()
    
    @pytest.mark.asyncio
    async def test_create_tool_proxy_success(self, factory):
        """Test successful tool proxy creation."""
        with patch('contexa_sdk.mcp.client.proxy_factory.MCPToolProxy') as mock_tool_proxy:
            mock_proxy = AsyncMock()
            mock_tool_proxy.return_value = mock_proxy
            
            proxy = await factory.create_tool_proxy("calculator")
            
            assert proxy == mock_proxy
            mock_proxy.initialize.assert_called_once()
            assert "tool:calculator" in factory.proxies
    
    @pytest.mark.asyncio
    async def test_create_tool_proxy_empty_name(self, factory):
        """Test tool proxy creation with empty name."""
        with pytest.raises(ValueError, match="Tool name cannot be empty"):
            await factory.create_tool_proxy("")
    
    @pytest.mark.asyncio
    async def test_create_tool_proxy_factory_closed(self, factory):
        """Test tool proxy creation when factory is closed."""
        factory._closed = True
        
        with pytest.raises(MCPProxyError, match="Factory is closed"):
            await factory.create_tool_proxy("calculator")
    
    @pytest.mark.asyncio
    async def test_create_tool_proxy_existing(self, factory):
        """Test creating tool proxy that already exists."""
        mock_proxy = AsyncMock()
        factory.proxies["tool:calculator"] = mock_proxy
        
        proxy = await factory.create_tool_proxy("calculator")
        
        assert proxy == mock_proxy
        # Should not create new proxy or call initialize
        mock_proxy.initialize.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_tool_proxy_initialization_failure(self, factory):
        """Test tool proxy creation with initialization failure."""
        with patch('contexa_sdk.mcp.client.proxy_factory.MCPToolProxy') as mock_tool_proxy:
            mock_proxy = AsyncMock()
            mock_proxy.initialize.side_effect = Exception("Init failed")
            mock_tool_proxy.return_value = mock_proxy
            
            with pytest.raises(MCPProxyError, match="Tool proxy creation failed"):
                await factory.create_tool_proxy("calculator")
    
    @pytest.mark.asyncio
    async def test_create_resource_proxy_success(self, factory):
        """Test successful resource proxy creation."""
        with patch('contexa_sdk.mcp.client.proxy_factory.MCPResourceProxy') as mock_resource_proxy:
            mock_proxy = AsyncMock()
            mock_resource_proxy.return_value = mock_proxy
            
            proxy = await factory.create_resource_proxy()
            
            assert proxy == mock_proxy
            mock_proxy.initialize.assert_called_once()
            assert "resource:default" in factory.proxies
    
    @pytest.mark.asyncio
    async def test_create_resource_proxy_existing(self, factory):
        """Test creating resource proxy that already exists."""
        mock_proxy = AsyncMock()
        factory.proxies["resource:default"] = mock_proxy
        
        proxy = await factory.create_resource_proxy()
        
        assert proxy == mock_proxy
        mock_proxy.initialize.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_prompt_proxy_success(self, factory):
        """Test successful prompt proxy creation."""
        with patch('contexa_sdk.mcp.client.proxy_factory.MCPPromptProxy') as mock_prompt_proxy:
            mock_proxy = AsyncMock()
            mock_prompt_proxy.return_value = mock_proxy
            
            proxy = await factory.create_prompt_proxy()
            
            assert proxy == mock_proxy
            mock_proxy.initialize.assert_called_once()
            assert "prompt:default" in factory.proxies
    
    @pytest.mark.asyncio
    async def test_create_prompt_proxy_custom_config(self, factory):
        """Test prompt proxy creation with custom config."""
        custom_config = MCPProxyConfig(server_url="http://custom:8000")
        
        with patch('contexa_sdk.mcp.client.proxy_factory.MCPPromptProxy') as mock_prompt_proxy:
            mock_proxy = AsyncMock()
            mock_prompt_proxy.return_value = mock_proxy
            
            proxy = await factory.create_prompt_proxy(custom_config)
            
            mock_prompt_proxy.assert_called_once_with(custom_config)
            assert proxy == mock_proxy
    
    @pytest.mark.asyncio
    async def test_get_tool_proxy(self, factory):
        """Test getting existing tool proxy."""
        mock_proxy = AsyncMock()
        factory.proxies["tool:calculator"] = mock_proxy
        
        proxy = await factory.get_tool_proxy("calculator")
        assert proxy == mock_proxy
        
        # Non-existent proxy
        proxy = await factory.get_tool_proxy("nonexistent")
        assert proxy is None
    
    @pytest.mark.asyncio
    async def test_get_resource_proxy(self, factory):
        """Test getting existing resource proxy."""
        mock_proxy = AsyncMock()
        factory.proxies["resource:default"] = mock_proxy
        
        proxy = await factory.get_resource_proxy()
        assert proxy == mock_proxy
        
        # No existing proxy
        factory.proxies.clear()
        proxy = await factory.get_resource_proxy()
        assert proxy is None
    
    @pytest.mark.asyncio
    async def test_get_prompt_proxy(self, factory):
        """Test getting existing prompt proxy."""
        mock_proxy = AsyncMock()
        factory.proxies["prompt:default"] = mock_proxy
        
        proxy = await factory.get_prompt_proxy()
        assert proxy == mock_proxy
        
        # No existing proxy
        factory.proxies.clear()
        proxy = await factory.get_prompt_proxy()
        assert proxy is None
    
    @pytest.mark.asyncio
    async def test_discover_capabilities(self, factory):
        """Test capability discovery."""
        # Mock resource proxy
        mock_resource_proxy = AsyncMock()
        mock_resources = [
            MagicMock(uri="file://test1.txt"),
            MagicMock(uri="file://test2.txt")
        ]
        mock_resource_proxy.list_resources.return_value = mock_resources
        
        # Mock prompt proxy
        mock_prompt_proxy = AsyncMock()
        mock_prompts = [
            MagicMock(name="summarize"),
            MagicMock(name="translate")
        ]
        # Set the name attribute properly
        mock_prompts[0].name = "summarize"
        mock_prompts[1].name = "translate"
        mock_prompt_proxy.list_prompts.return_value = mock_prompts
        
        with patch.object(factory, 'create_resource_proxy', return_value=mock_resource_proxy), \
             patch.object(factory, 'create_prompt_proxy', return_value=mock_prompt_proxy), \
             patch.object(factory, 'create_tool_proxy', side_effect=Exception("Expected")):
            
            capabilities = await factory.discover_capabilities()
            
            assert capabilities["tools"] == []  # Tool discovery expected to fail
            assert capabilities["resources"] == ["file://test1.txt", "file://test2.txt"]
            assert capabilities["prompts"] == ["summarize", "translate"]
    
    @pytest.mark.asyncio
    async def test_discover_capabilities_failure(self, factory):
        """Test capability discovery with failures."""
        with patch.object(factory, 'create_resource_proxy', side_effect=Exception("Resource error")), \
             patch.object(factory, 'create_prompt_proxy', side_effect=Exception("Prompt error")), \
             patch.object(factory, 'create_tool_proxy', side_effect=Exception("Tool error")):
            
            capabilities = await factory.discover_capabilities()
            
            # Should handle failures gracefully
            assert capabilities["tools"] == []
            assert capabilities["resources"] == []
            assert capabilities["prompts"] == []
    
    @pytest.mark.asyncio
    async def test_validate_connection_success(self, factory):
        """Test successful connection validation."""
        mock_resource_proxy = AsyncMock()
        
        with patch.object(factory, 'create_resource_proxy', return_value=mock_resource_proxy):
            result = await factory.validate_connection()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, factory):
        """Test connection validation failure."""
        with patch.object(factory, 'create_resource_proxy', side_effect=Exception("Connection failed")):
            result = await factory.validate_connection()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_clear_caches(self, factory):
        """Test clearing caches for all proxies."""
        mock_proxy1 = MagicMock()
        mock_proxy2 = MagicMock()
        mock_proxy3 = MagicMock()  # No clear_cache method
        del mock_proxy3.clear_cache
        
        factory.proxies["proxy1"] = mock_proxy1
        factory.proxies["proxy2"] = mock_proxy2
        factory.proxies["proxy3"] = mock_proxy3
        
        await factory.clear_caches()
        
        mock_proxy1.clear_cache.assert_called_once()
        mock_proxy2.clear_cache.assert_called_once()
        # mock_proxy3 should not cause an error
    
    @pytest.mark.asyncio
    async def test_close(self, factory):
        """Test factory closure."""
        mock_proxy1 = AsyncMock()
        mock_proxy2 = AsyncMock()
        mock_proxy2.close.side_effect = Exception("Close error")  # Should handle errors
        
        factory.proxies["proxy1"] = mock_proxy1
        factory.proxies["proxy2"] = mock_proxy2
        
        await factory.close()
        
        mock_proxy1.close.assert_called_once()
        mock_proxy2.close.assert_called_once()
        assert factory.proxies == {}
        assert factory.is_closed()
        
        # Second close should be safe
        await factory.close()
    
    def test_get_proxy_count(self, factory):
        """Test getting proxy count."""
        assert factory.get_proxy_count() == 0
        
        factory.proxies["proxy1"] = MagicMock()
        factory.proxies["proxy2"] = MagicMock()
        
        assert factory.get_proxy_count() == 2
    
    def test_get_proxy_keys(self, factory):
        """Test getting proxy keys."""
        assert factory.get_proxy_keys() == []
        
        factory.proxies["proxy1"] = MagicMock()
        factory.proxies["proxy2"] = MagicMock()
        
        keys = factory.get_proxy_keys()
        assert set(keys) == {"proxy1", "proxy2"}
    
    def test_is_closed(self, factory):
        """Test checking if factory is closed."""
        assert not factory.is_closed()
        
        factory._closed = True
        assert factory.is_closed()


class TestMCPProxyManager:
    """Test MCPProxyManager class."""
    
    @pytest.fixture
    def server_configs(self):
        """Create test server configurations."""
        return [
            MCPProxyConfig(server_url="http://server1:8000"),
            MCPProxyConfig(server_url="http://server2:8000"),
            MCPProxyConfig(server_url="http://server3:8000")
        ]
    
    @pytest.fixture
    def manager(self, server_configs):
        """Create test proxy manager."""
        return MCPProxyManager(server_configs)
    
    def test_manager_initialization(self, server_configs):
        """Test manager initialization."""
        manager = MCPProxyManager(server_configs)
        
        assert manager.server_configs == server_configs
        assert manager.factories == {}
        assert manager._current_server_index == 0
        assert manager.logger is not None
    
    @pytest.mark.asyncio
    async def test_get_factory_specific_server(self, manager):
        """Test getting factory for specific server."""
        with patch('contexa_sdk.mcp.client.proxy_factory.MCPProxyFactory') as mock_factory_class:
            mock_factory = AsyncMock()
            mock_factory_class.return_value = mock_factory
            
            factory = await manager.get_factory("http://server1:8000")
            
            assert factory == mock_factory
            assert "http://server1:8000" in manager.factories
            mock_factory_class.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_factory_specific_server_existing(self, manager):
        """Test getting factory for specific server that already exists."""
        mock_factory = AsyncMock()
        manager.factories["http://server1:8000"] = mock_factory
        
        factory = await manager.get_factory("http://server1:8000")
        
        assert factory == mock_factory
    
    @pytest.mark.asyncio
    async def test_get_factory_specific_server_not_configured(self, manager):
        """Test getting factory for server not in configuration."""
        with pytest.raises(MCPProxyError, match="No configuration found for server"):
            await manager.get_factory("http://unknown:8000")
    
    @pytest.mark.asyncio
    async def test_get_factory_load_balanced(self, manager):
        """Test getting factory with load balancing."""
        with patch('contexa_sdk.mcp.client.proxy_factory.MCPProxyFactory') as mock_factory_class:
            mock_factory1 = AsyncMock()
            mock_factory1.validate_connection.return_value = True
            mock_factory_class.return_value = mock_factory1
            
            # First call should get server1
            factory1 = await manager.get_factory()
            assert factory1 == mock_factory1
            assert manager._current_server_index == 1
            
            # Second call should get server2 (but we'll return the same mock)
            factory2 = await manager.get_factory()
            assert factory2 == mock_factory1
            assert manager._current_server_index == 2
    
    @pytest.mark.asyncio
    async def test_get_factory_load_balanced_unhealthy_servers(self, manager):
        """Test load balancing with unhealthy servers."""
        with patch('contexa_sdk.mcp.client.proxy_factory.MCPProxyFactory') as mock_factory_class:
            mock_factory = AsyncMock()
            mock_factory.validate_connection.return_value = False  # All servers unhealthy
            mock_factory_class.return_value = mock_factory
            
            with pytest.raises(MCPProxyError, match="No healthy servers available"):
                await manager.get_factory()
    
    @pytest.mark.asyncio
    async def test_get_factory_load_balanced_mixed_health(self, manager):
        """Test load balancing with mixed server health."""
        with patch('contexa_sdk.mcp.client.proxy_factory.MCPProxyFactory') as mock_factory_class:
            # First two servers unhealthy, third healthy
            mock_factory_unhealthy = AsyncMock()
            mock_factory_unhealthy.validate_connection.return_value = False
            
            mock_factory_healthy = AsyncMock()
            mock_factory_healthy.validate_connection.return_value = True
            
            # Return unhealthy for first two calls, healthy for third
            mock_factory_class.side_effect = [
                mock_factory_unhealthy,  # server1
                mock_factory_unhealthy,  # server2
                mock_factory_healthy     # server3
            ]
            
            factory = await manager.get_factory()
            
            assert factory == mock_factory_healthy
            # Should have tried all three servers
            assert mock_factory_class.call_count == 3
    
    @pytest.mark.asyncio
    async def test_close(self, manager):
        """Test manager closure."""
        mock_factory1 = AsyncMock()
        mock_factory2 = AsyncMock()
        
        manager.factories["server1"] = mock_factory1
        manager.factories["server2"] = mock_factory2
        
        await manager.close()
        
        mock_factory1.close.assert_called_once()
        mock_factory2.close.assert_called_once()
        assert manager.factories == {}


class TestCreateMCPProxyFactory:
    """Test create_mcp_proxy_factory context manager."""
    
    @pytest.mark.asyncio
    async def test_context_manager_success(self):
        """Test successful context manager usage."""
        config = MCPProxyConfig(server_url="http://localhost:8000")
        
        with patch('contexa_sdk.mcp.client.proxy_factory.MCPProxyFactory') as mock_factory_class:
            mock_factory = AsyncMock()
            mock_factory_class.return_value = mock_factory
            
            async with create_mcp_proxy_factory(config) as factory:
                assert factory == mock_factory
            
            # Factory should be closed after context exit
            mock_factory.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager_exception(self):
        """Test context manager with exception."""
        config = MCPProxyConfig(server_url="http://localhost:8000")
        
        with patch('contexa_sdk.mcp.client.proxy_factory.MCPProxyFactory') as mock_factory_class:
            mock_factory = AsyncMock()
            mock_factory_class.return_value = mock_factory
            
            with pytest.raises(ValueError, match="Test error"):
                async with create_mcp_proxy_factory(config) as factory:
                    raise ValueError("Test error")
            
            # Factory should still be closed after exception
            mock_factory.close.assert_called_once()


class TestIntegrationScenarios:
    """Test integration scenarios with multiple components."""
    
    @pytest.mark.asyncio
    async def test_factory_lifecycle_management(self):
        """Test complete factory lifecycle with multiple proxies."""
        config = MCPProxyConfig(server_url="http://localhost:8000")
        factory = MCPProxyFactory(config)
        
        with patch('contexa_sdk.mcp.client.proxy_factory.MCPToolProxy') as mock_tool_proxy, \
             patch('contexa_sdk.mcp.client.proxy_factory.MCPResourceProxy') as mock_resource_proxy, \
             patch('contexa_sdk.mcp.client.proxy_factory.MCPPromptProxy') as mock_prompt_proxy:
            
            # Create mock proxies
            mock_tool = AsyncMock()
            mock_resource = AsyncMock()
            mock_prompt = AsyncMock()
            
            mock_tool_proxy.return_value = mock_tool
            mock_resource_proxy.return_value = mock_resource
            mock_prompt_proxy.return_value = mock_prompt
            
            # Create proxies
            tool_proxy = await factory.create_tool_proxy("calculator")
            resource_proxy = await factory.create_resource_proxy()
            prompt_proxy = await factory.create_prompt_proxy()
            
            # Verify proxies are created and initialized
            assert tool_proxy == mock_tool
            assert resource_proxy == mock_resource
            assert prompt_proxy == mock_prompt
            
            mock_tool.initialize.assert_called_once()
            mock_resource.initialize.assert_called_once()
            mock_prompt.initialize.assert_called_once()
            
            # Verify factory state
            assert factory.get_proxy_count() == 3
            assert set(factory.get_proxy_keys()) == {
                "tool:calculator", "resource:default", "prompt:default"
            }
            
            # Clear caches
            await factory.clear_caches()
            mock_tool.clear_cache.assert_called_once()
            mock_resource.clear_cache.assert_called_once()
            mock_prompt.clear_cache.assert_called_once()
            
            # Close factory
            await factory.close()
            mock_tool.close.assert_called_once()
            mock_resource.close.assert_called_once()
            mock_prompt.close.assert_called_once()
            
            assert factory.is_closed()
            assert factory.get_proxy_count() == 0
    
    @pytest.mark.asyncio
    async def test_manager_with_factory_operations(self):
        """Test manager operations with factory creation and proxy management."""
        server_configs = [
            MCPProxyConfig(server_url="http://server1:8000"),
            MCPProxyConfig(server_url="http://server2:8000")
        ]
        manager = MCPProxyManager(server_configs)
        
        with patch('contexa_sdk.mcp.client.proxy_factory.MCPProxyFactory') as mock_factory_class:
            mock_factory1 = AsyncMock()
            mock_factory1.validate_connection.return_value = True
            mock_factory2 = AsyncMock()
            mock_factory2.validate_connection.return_value = True
            
            mock_factory_class.side_effect = [mock_factory1, mock_factory2]
            
            # Get factories for different servers
            factory1 = await manager.get_factory("http://server1:8000")
            factory2 = await manager.get_factory("http://server2:8000")
            
            assert factory1 == mock_factory1
            assert factory2 == mock_factory2
            assert len(manager.factories) == 2
            
            # Load balanced access should return healthy server
            factory_lb = await manager.get_factory()
            assert factory_lb in [mock_factory1, mock_factory2]
            
            # Close manager
            await manager.close()
            mock_factory1.close.assert_called_once()
            mock_factory2.close.assert_called_once()
            assert len(manager.factories) == 0 