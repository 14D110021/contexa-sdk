"""
Unit tests for MCP integration module.

This module tests the MCPIntegration class and convenience functions
for seamless agent-to-MCP conversion.
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.mcp.client.integration import (
    MCPIntegration, MCPIntegrationConfig,
    integrate_mcp_server_with_agent, create_multi_agent_mcp_server
)
from contexa_sdk.mcp.server import MCPServer


class TestTool(ContexaTool):
    """Test tool for integration testing."""
    
    def __init__(self, name: str = "test_tool"):
        self.name = name
        self.description = f"Test tool: {name}"
        self.parameters_schema = {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input parameter"}
            },
            "required": ["input"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute the test tool."""
        return f"Test result for {arguments.get('input', 'no input')}"


class TestMCPIntegrationConfig:
    """Test cases for MCPIntegrationConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MCPIntegrationConfig()
        
        assert config.server_name is None
        assert config.server_description is None
        assert config.transport_type == "stdio"
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.auto_map_tools is True
        assert config.auto_map_prompts is True
        assert config.auto_create_resources is True
        assert config.create_agent_info_resource is True
        assert config.create_tool_list_resource is True
        assert config.create_capability_resource is True
        assert config.enable_integration_logging is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = MCPIntegrationConfig(
            server_name="Custom Server",
            transport_type="http",
            port=9000,
            auto_map_tools=False,
            enable_integration_logging=False
        )
        
        assert config.server_name == "Custom Server"
        assert config.transport_type == "http"
        assert config.port == 9000
        assert config.auto_map_tools is False
        assert config.enable_integration_logging is False


class TestMCPIntegration:
    """Test cases for MCPIntegration class."""
    
    @pytest.fixture
    def integration_config(self):
        """Create a test integration configuration."""
        return MCPIntegrationConfig(
            server_name="Test Server",
            transport_type="stdio",
            enable_integration_logging=True
        )
    
    @pytest.fixture
    def integration(self, integration_config):
        """Create an MCPIntegration instance for testing."""
        return MCPIntegration(integration_config)
    
    @pytest.fixture
    def test_agent(self):
        """Create a test agent."""
        tool = TestTool("calculator")
        model = ContexaModel(model_name="gpt-4o", provider="openai")
        
        agent = ContexaAgent(
            name="Test Agent",
            description="A test agent for integration testing",
            model=model,
            tools=[tool]
        )
        return agent
    
    def test_initialization(self, integration_config):
        """Test MCPIntegration initialization."""
        integration = MCPIntegration(integration_config)
        
        assert integration.config == integration_config
        assert len(integration.integrated_agents) == 0
        assert len(integration.created_servers) == 0
        assert len(integration.capability_mappings) == 0
    
    def test_initialization_with_default_config(self):
        """Test MCPIntegration initialization with default config."""
        integration = MCPIntegration()
        
        assert isinstance(integration.config, MCPIntegrationConfig)
        assert integration.config.transport_type == "stdio"
    
    @pytest.mark.asyncio
    async def test_extract_agent_capabilities(self, integration, test_agent):
        """Test capability extraction from agent."""
        capabilities = await integration._extract_agent_capabilities(test_agent)
        
        assert "tools" in capabilities
        assert "model_info" in capabilities
        assert "metadata" in capabilities
        
        # Check tools
        assert len(capabilities["tools"]) == 1
        tool_info = capabilities["tools"][0]
        assert tool_info["name"] == "calculator"
        assert tool_info["description"] == "Test tool: calculator"
        assert "parameters" in tool_info
        
        # Check model info
        model_info = capabilities["model_info"]
        assert model_info["provider"] == "openai"
        assert model_info["model_name"] == "gpt-4o"
        assert "text_generation" in model_info["capabilities"]
        
        # Check metadata
        metadata = capabilities["metadata"]
        assert metadata["name"] == "Test Agent"
        assert metadata["description"] == "A test agent for integration testing"
        assert metadata["tool_count"] == 1
        assert metadata["created_by"] == "contexa_sdk_integration"
    
    @pytest.mark.asyncio
    async def test_create_server_config(self, integration, test_agent):
        """Test server configuration creation."""
        capabilities = await integration._extract_agent_capabilities(test_agent)
        config = await integration._create_server_config(test_agent, "TestAgent", capabilities)
        
        assert config.name == "Test Server"  # From integration config
        assert config.description == "MCP server exposing TestAgent capabilities"
        assert config.transport_type == "stdio"
        assert config.enable_sampling is True
        assert config.enable_logging is True
    
    @pytest.mark.asyncio
    async def test_integrate_agent(self, integration, test_agent):
        """Test agent integration."""
        server = await integration.integrate_agent(test_agent, "TestAgent")
        
        assert isinstance(server, MCPServer)
        assert "TestAgent" in integration.integrated_agents
        assert "TestAgent" in integration.created_servers
        assert "TestAgent" in integration.capability_mappings
        
        # Check that agent is registered with server
        assert "TestAgent" in server.agents
        assert len(server.tools) == 1
        assert "calculator" in server.tools
    
    @pytest.mark.asyncio
    async def test_integrate_agent_with_auto_name(self, integration, test_agent):
        """Test agent integration with automatic name generation."""
        server = await integration.integrate_agent(test_agent)
        
        assert isinstance(server, MCPServer)
        assert "Test Agent" in integration.integrated_agents
    
    @pytest.mark.asyncio
    async def test_integrate_agent_without_name(self, integration):
        """Test agent integration without name."""
        tool = TestTool("test_tool")
        model = ContexaModel(model_name="gpt-4o", provider="openai")
        agent = ContexaAgent(
            tools=[tool],
            model=model,
            description="Agent without name"
        )
        
        server = await integration.integrate_agent(agent)
        
        assert isinstance(server, MCPServer)
        assert "unnamed_agent" in integration.integrated_agents
    
    @pytest.mark.asyncio
    async def test_start_stop_server(self, integration, test_agent):
        """Test starting and stopping integrated servers."""
        server = await integration.integrate_agent(test_agent, "TestAgent")
        
        # Mock the server start/stop methods
        server.start = AsyncMock()
        server.stop = AsyncMock()
        
        # Test start
        await integration.start_server("TestAgent")
        server.start.assert_called_once()
        
        # Test stop
        await integration.stop_server("TestAgent")
        server.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_nonexistent_server(self, integration):
        """Test starting a non-existent server."""
        with pytest.raises(ValueError, match="No server found for agent"):
            await integration.start_server("NonExistent")
    
    @pytest.mark.asyncio
    async def test_stop_all_servers(self, integration, test_agent):
        """Test stopping all servers."""
        # Create multiple servers
        server1 = await integration.integrate_agent(test_agent, "Agent1")
        server2 = await integration.integrate_agent(test_agent, "Agent2")
        
        # Mock stop methods
        server1.stop = AsyncMock()
        server2.stop = AsyncMock()
        
        await integration.stop_all_servers()
        
        server1.stop.assert_called_once()
        server2.stop.assert_called_once()
    
    def test_get_server(self, integration, test_agent):
        """Test getting server for an agent."""
        # Test non-existent server
        assert integration.get_server("NonExistent") is None
    
    @pytest.mark.asyncio
    async def test_get_integration_info(self, integration, test_agent):
        """Test getting integration information."""
        server = await integration.integrate_agent(test_agent, "TestAgent")
        
        info = integration.get_integration_info("TestAgent")
        
        assert info is not None
        assert info["agent"] == test_agent
        assert info["server"] == server
        assert "capabilities" in info
        assert "server_info" in info
        assert "running" in info
        
        # Test non-existent agent
        assert integration.get_integration_info("NonExistent") is None
    
    @pytest.mark.asyncio
    async def test_list_integrated_agents(self, integration, test_agent):
        """Test listing integrated agents."""
        assert integration.list_integrated_agents() == []
        
        await integration.integrate_agent(test_agent, "Agent1")
        await integration.integrate_agent(test_agent, "Agent2")
        
        agents = integration.list_integrated_agents()
        assert len(agents) == 2
        assert "Agent1" in agents
        assert "Agent2" in agents


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    @pytest.fixture
    def test_agent(self):
        """Create a test agent."""
        tool = TestTool("test_tool")
        model = ContexaModel(model_name="gpt-4o", provider="openai")
        
        agent = ContexaAgent(
            name="Test Agent",
            description="A test agent",
            model=model,
            tools=[tool]
        )
        return agent
    
    @pytest.mark.asyncio
    async def test_integrate_mcp_server_with_agent(self, test_agent):
        """Test the convenience function for agent integration."""
        server = await integrate_mcp_server_with_agent(test_agent)
        
        assert isinstance(server, MCPServer)
        assert "Test Agent" in server.agents
        assert len(server.tools) == 1
        assert server.running is False  # Not auto-started
    
    @pytest.mark.asyncio
    async def test_integrate_mcp_server_with_agent_custom_name(self, test_agent):
        """Test integration with custom agent name."""
        server = await integrate_mcp_server_with_agent(test_agent, agent_name="CustomAgent")
        
        assert isinstance(server, MCPServer)
        assert "CustomAgent" in server.agents
    
    @pytest.mark.asyncio
    async def test_integrate_mcp_server_with_agent_auto_start(self, test_agent):
        """Test integration with auto-start."""
        with patch.object(MCPServer, 'start', new_callable=AsyncMock) as mock_start:
            server = await integrate_mcp_server_with_agent(test_agent, auto_start=True)
            mock_start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_integrate_mcp_server_with_agent_custom_config(self, test_agent):
        """Test integration with custom configuration."""
        config = MCPIntegrationConfig(
            server_name="Custom Server",
            transport_type="http",
            port=9000
        )
        
        server = await integrate_mcp_server_with_agent(test_agent, config=config)
        
        assert server.config.name == "Custom Server"
        assert server.config.transport_type == "http"
        assert server.config.port == 9000
    
    @pytest.mark.asyncio
    async def test_integrate_mcp_server_with_none_agent(self):
        """Test integration with None agent."""
        with pytest.raises(ValueError, match="Agent cannot be None"):
            await integrate_mcp_server_with_agent(None)
    
    @pytest.mark.asyncio
    async def test_integrate_mcp_server_with_default_name(self):
        """Test integration with agent using default name."""
        tool = TestTool("test_tool")
        model = ContexaModel(model_name="gpt-4o", provider="openai")
        agent = ContexaAgent(
            tools=[tool],
            model=model,
            description="Agent without name"
        )
        
        # This should work since ContexaAgent provides a default name "unnamed_agent"
        server = await integrate_mcp_server_with_agent(agent)
        assert isinstance(server, MCPServer)
        assert "unnamed_agent" in server.agents
    
    @pytest.mark.asyncio
    async def test_create_multi_agent_mcp_server(self):
        """Test creating multi-agent MCP server."""
        tool1 = TestTool("tool1")
        tool2 = TestTool("tool2")
        model = ContexaModel(model_name="gpt-4o", provider="openai")
        
        agent1 = ContexaAgent(name="Agent1", model=model, tools=[tool1])
        agent2 = ContexaAgent(name="Agent2", model=model, tools=[tool2])
        
        server = await create_multi_agent_mcp_server([agent1, agent2])
        
        assert isinstance(server, MCPServer)
        assert len(server.agents) == 2
        assert "Agent1" in server.agents
        assert "Agent2" in server.agents
        assert len(server.tools) == 2
        assert "tool1" in server.tools
        assert "tool2" in server.tools
    
    @pytest.mark.asyncio
    async def test_create_multi_agent_mcp_server_custom_name(self):
        """Test creating multi-agent server with custom name."""
        tool = TestTool("tool")
        model = ContexaModel(model_name="gpt-4o", provider="openai")
        agent = ContexaAgent(name="Agent", model=model, tools=[tool])
        
        server = await create_multi_agent_mcp_server([agent], server_name="Custom Multi-Agent Server")
        
        assert server.config.name == "Custom Multi-Agent Server"
    
    @pytest.mark.asyncio
    async def test_create_multi_agent_mcp_server_empty_list(self):
        """Test creating multi-agent server with empty agent list."""
        with pytest.raises(ValueError, match="Agents list cannot be empty"):
            await create_multi_agent_mcp_server([])


if __name__ == "__main__":
    pytest.main([__file__]) 