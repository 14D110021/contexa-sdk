"""
End-to-end integration tests for MCP client integration.

This module tests the complete workflow from Contexa agent creation
to MCP server integration and actual MCP protocol operations.
"""

import pytest
import asyncio
import json
from typing import Dict, Any

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.mcp.client.integration import (
    integrate_mcp_server_with_agent, create_multi_agent_mcp_server,
    MCPIntegrationConfig
)
from contexa_sdk.mcp.server.protocol import MCPRequest


class CalculatorTool(ContexaTool):
    """Calculator tool for end-to-end testing."""
    
    def __init__(self):
        self.name = "calculator"
        self.description = "Perform basic arithmetic operations"
        self.parameters_schema = {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string", 
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The arithmetic operation to perform"
                },
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["operation", "a", "b"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute the calculator operation."""
        operation = arguments["operation"]
        a = arguments["a"]
        b = arguments["b"]
        
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero")
            result = a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return f"Result: {a} {operation} {b} = {result}"


class WeatherTool(ContexaTool):
    """Weather tool for end-to-end testing."""
    
    def __init__(self):
        self.name = "get_weather"
        self.description = "Get weather information for a location"
        self.parameters_schema = {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "The location to get weather for"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius"}
            },
            "required": ["location"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute the weather lookup."""
        location = arguments["location"]
        unit = arguments.get("unit", "celsius")
        
        # Mock weather data
        temp = 22 if unit == "celsius" else 72
        return f"Weather in {location}: Sunny, {temp}°{unit.upper()}"


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    @pytest.fixture
    async def calculator_agent(self):
        """Create a calculator agent for testing."""
        tool = CalculatorTool()
        model = ContexaModel(model_name="gpt-4o", provider="openai")
        
        agent = ContexaAgent(
            name="Calculator Agent",
            description="An agent that can perform arithmetic calculations",
            model=model,
            tools=[tool],
            system_prompt="You are a helpful calculator assistant."
        )
        return agent
    
    @pytest.fixture
    async def weather_agent(self):
        """Create a weather agent for testing."""
        tool = WeatherTool()
        model = ContexaModel(model_name="gpt-4o", provider="openai")
        
        agent = ContexaAgent(
            name="Weather Agent",
            description="An agent that provides weather information",
            model=model,
            tools=[tool],
            system_prompt="You are a helpful weather assistant."
        )
        return agent
    
    @pytest.mark.asyncio
    async def test_single_agent_integration_workflow(self, calculator_agent):
        """Test complete workflow for single agent integration."""
        # Step 1: Integrate agent to MCP server
        server = await integrate_mcp_server_with_agent(calculator_agent)
        
        try:
            # Verify server is created correctly
            assert server is not None
            assert "Calculator Agent" in server.agents
            assert len(server.tools) == 1
            assert "calculator" in server.tools
            
            # Step 2: Initialize handlers (simulating server startup)
            for handler in server.handlers.values():
                await handler.initialize()
            
            # Step 3: Test MCP protocol operations
            
            # Test tools/list
            tools_request = MCPRequest(method="tools/list", id="test_tools_list")
            tools_response = await server._handle_list_tools(tools_request)
            
            assert "tools" in tools_response
            assert len(tools_response["tools"]) == 1
            tool_info = tools_response["tools"][0]
            assert tool_info["name"] == "calculator"
            assert tool_info["description"] == "Perform basic arithmetic operations"
            assert "inputSchema" in tool_info
            
            # Test tools/call
            call_request = MCPRequest(
                method="tools/call",
                id="test_tool_call",
                params={
                    "name": "calculator",
                    "arguments": {
                        "operation": "add",
                        "a": 15,
                        "b": 25
                    }
                }
            )
            call_response = await server._handle_call_tool(call_request)
            
            assert "content" in call_response
            assert call_response["isError"] is False
            assert "Result: 15 add 25 = 40" in call_response["content"][0]["text"]
            
            # Test resources/list
            resources_request = MCPRequest(method="resources/list", id="test_resources_list")
            resources_response = await server._handle_list_resources(resources_request)
            
            assert "resources" in resources_response
            resources = resources_response["resources"]
            assert len(resources) >= 2  # At least system resources
            
            # Find agent-specific resources
            agent_info_resource = None
            for resource in resources:
                if resource["uri"] == "agent://Calculator Agent/info":
                    agent_info_resource = resource
                    break
            
            assert agent_info_resource is not None
            assert agent_info_resource["name"] == "Calculator Agent Information"
            
            # Test resources/read for agent info
            read_request = MCPRequest(
                method="resources/read",
                id="test_resource_read",
                params={"uri": "agent://Calculator Agent/info"}
            )
            read_response = await server._handle_read_resource(read_request)
            
            assert "contents" in read_response
            content = json.loads(read_response["contents"][0]["text"])
            assert content["name"] == "Calculator Agent"
            assert content["description"] == "An agent that can perform arithmetic calculations"
            assert "capabilities" in content
            
            # Test prompts/list
            prompts_request = MCPRequest(method="prompts/list", id="test_prompts_list")
            prompts_response = await server._handle_list_prompts(prompts_request)
            
            assert "prompts" in prompts_response
            assert len(prompts_response["prompts"]) >= 2  # Default prompts
            
            # Test sampling/createMessage
            sampling_request = MCPRequest(
                method="sampling/createMessage",
                id="test_sampling",
                params={
                    "messages": [
                        {"role": "user", "content": {"type": "text", "text": "Calculate 10 + 5"}}
                    ],
                    "systemPrompt": "You are a calculator assistant",
                    "temperature": 0.7
                }
            )
            sampling_response = await server._handle_create_message(sampling_request)
            
            assert "role" in sampling_response
            assert sampling_response["role"] == "assistant"
            assert "content" in sampling_response
            assert "_meta" in sampling_response
            
        finally:
            # Cleanup
            if server.running:
                await server.stop()
    
    @pytest.mark.asyncio
    async def test_multi_agent_integration_workflow(self, calculator_agent, weather_agent):
        """Test complete workflow for multi-agent integration."""
        # Step 1: Create multi-agent MCP server
        server = await create_multi_agent_mcp_server(
            [calculator_agent, weather_agent],
            server_name="Multi-Agent Test Server"
        )
        
        try:
            # Verify server is created correctly
            assert server is not None
            assert len(server.agents) == 2
            assert "Calculator Agent" in server.agents
            assert "Weather Agent" in server.agents
            assert len(server.tools) == 2
            assert "calculator" in server.tools
            assert "get_weather" in server.tools
            
            # Step 2: Initialize handlers
            for handler in server.handlers.values():
                await handler.initialize()
            
            # Step 3: Test tools from both agents
            
            # Test calculator tool
            calc_request = MCPRequest(
                method="tools/call",
                id="test_calc",
                params={
                    "name": "calculator",
                    "arguments": {
                        "operation": "multiply",
                        "a": 7,
                        "b": 8
                    }
                }
            )
            calc_response = await server._handle_call_tool(calc_request)
            
            assert calc_response["isError"] is False
            assert "Result: 7 multiply 8 = 56" in calc_response["content"][0]["text"]
            
            # Test weather tool
            weather_request = MCPRequest(
                method="tools/call",
                id="test_weather",
                params={
                    "name": "get_weather",
                    "arguments": {
                        "location": "New York",
                        "unit": "fahrenheit"
                    }
                }
            )
            weather_response = await server._handle_call_tool(weather_request)
            
            assert weather_response["isError"] is False
            assert "Weather in New York: Sunny, 72°FAHRENHEIT" in weather_response["content"][0]["text"]
            
            # Test tools/list shows both tools
            tools_request = MCPRequest(method="tools/list", id="test_tools")
            tools_response = await server._handle_list_tools(tools_request)
            
            assert len(tools_response["tools"]) == 2
            tool_names = [tool["name"] for tool in tools_response["tools"]]
            assert "calculator" in tool_names
            assert "get_weather" in tool_names
            
        finally:
            # Cleanup
            if server.running:
                await server.stop()
    
    @pytest.mark.asyncio
    async def test_integration_with_custom_config(self, calculator_agent):
        """Test integration with custom configuration."""
        # Create custom configuration
        config = MCPIntegrationConfig(
            server_name="Custom Calculator Server",
            server_description="A custom MCP server for calculations",
            transport_type="http",
            port=9001,
            auto_create_resources=True,
            create_agent_info_resource=True,
            create_tool_list_resource=True,
            create_capability_resource=True
        )
        
        # Integrate with custom config
        server = await integrate_mcp_server_with_agent(
            calculator_agent,
            config=config,
            agent_name="CustomCalculator"
        )
        
        try:
            # Verify custom configuration is applied
            assert server.config.name == "Custom Calculator Server"
            assert server.config.description == "A custom MCP server for calculations"
            assert server.config.transport_type == "http"
            assert server.config.port == 9001
            
            # Verify agent is registered with custom name
            assert "CustomCalculator" in server.agents
            
            # Initialize handlers
            for handler in server.handlers.values():
                await handler.initialize()
            
            # Test that custom resources are created
            resources_request = MCPRequest(method="resources/list", id="test_resources")
            resources_response = await server._handle_list_resources(resources_request)
            
            resource_uris = [r["uri"] for r in resources_response["resources"]]
            assert "agent://CustomCalculator/info" in resource_uris
            assert "agent://CustomCalculator/tools" in resource_uris
            assert "agent://CustomCalculator/capabilities" in resource_uris
            
            # Test reading capability resource
            cap_request = MCPRequest(
                method="resources/read",
                id="test_capabilities",
                params={"uri": "agent://CustomCalculator/capabilities"}
            )
            cap_response = await server._handle_read_resource(cap_request)
            
            capabilities = json.loads(cap_response["contents"][0]["text"])
            assert "tools" in capabilities
            assert "model_info" in capabilities
            assert "metadata" in capabilities
            assert len(capabilities["tools"]) == 1
            assert capabilities["tools"][0]["name"] == "calculator"
            
        finally:
            # Cleanup
            if server.running:
                await server.stop()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_integration(self, calculator_agent):
        """Test error handling in the integration workflow."""
        server = await integrate_mcp_server_with_agent(calculator_agent)
        
        try:
            # Initialize handlers
            for handler in server.handlers.values():
                await handler.initialize()
            
            # Test calling non-existent tool
            invalid_tool_request = MCPRequest(
                method="tools/call",
                id="test_invalid_tool",
                params={
                    "name": "nonexistent_tool",
                    "arguments": {}
                }
            )
            error_response = await server._handle_call_tool(invalid_tool_request)
            
            assert error_response["isError"] is True
            assert "not found" in error_response["content"][0]["text"]
            
            # Test tool call with invalid arguments
            invalid_args_request = MCPRequest(
                method="tools/call",
                id="test_invalid_args",
                params={
                    "name": "calculator",
                    "arguments": {
                        "operation": "divide",
                        "a": 10,
                        "b": 0  # Division by zero
                    }
                }
            )
            div_zero_response = await server._handle_call_tool(invalid_args_request)
            
            assert div_zero_response["isError"] is True
            assert "Division by zero" in div_zero_response["content"][0]["text"]
            
            # Test reading non-existent resource
            invalid_resource_request = MCPRequest(
                method="resources/read",
                id="test_invalid_resource",
                params={"uri": "nonexistent://resource"}
            )
            
            with pytest.raises(ValueError, match="Resource not found"):
                await server._handle_read_resource(invalid_resource_request)
            
        finally:
            # Cleanup
            if server.running:
                await server.stop()
    
    @pytest.mark.asyncio
    async def test_resource_subscriptions(self, calculator_agent):
        """Test resource subscription functionality."""
        server = await integrate_mcp_server_with_agent(calculator_agent)
        
        try:
            # Initialize handlers
            for handler in server.handlers.values():
                await handler.initialize()
            
            # Test subscribing to a resource
            subscribe_request = MCPRequest(
                method="resources/subscribe",
                id="test_subscribe",
                params={"uri": "system://info"}
            )
            subscribe_response = await server._handle_subscribe_resource(subscribe_request)
            
            assert subscribe_response["success"] is True
            
            # Test unsubscribing from a resource
            unsubscribe_request = MCPRequest(
                method="resources/unsubscribe",
                id="test_unsubscribe",
                params={"uri": "system://info"}
            )
            unsubscribe_response = await server._handle_unsubscribe_resource(unsubscribe_request)
            
            assert unsubscribe_response["success"] is True
            
        finally:
            # Cleanup
            if server.running:
                await server.stop()
    
    @pytest.mark.asyncio
    async def test_server_lifecycle_management(self, calculator_agent):
        """Test server lifecycle management through integration."""
        from contexa_sdk.mcp.client.integration import MCPIntegration
        from unittest.mock import AsyncMock
        
        # Create integration instance
        integration = MCPIntegration()
        
        # Integrate agent
        server = await integration.integrate_agent(calculator_agent, "LifecycleTest")
        
        # Verify server is not running initially
        assert server.running is False
        
        # Mock the server start/stop methods to avoid transport issues
        server.start = AsyncMock()
        server.stop = AsyncMock()
        
        # Start server through integration
        await integration.start_server("LifecycleTest")
        server.start.assert_called_once()
        
        # Stop server through integration
        await integration.stop_server("LifecycleTest")
        server.stop.assert_called_once()
        
        # Test stopping all servers
        await integration.stop_all_servers()
        
        # Test integration info
        info = integration.get_integration_info("LifecycleTest")
        assert info is not None
        assert info["agent"] == calculator_agent
        assert info["server"] == server
        assert "capabilities" in info
        assert "server_info" in info


if __name__ == "__main__":
    pytest.main([__file__]) 