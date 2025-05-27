"""
Integration tests for MCP server with handlers.

This module tests the complete integration of MCP handlers with the MCP server,
ensuring all features work together correctly.
"""

import pytest
import asyncio
import json
from typing import Dict, Any

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.mcp.server import MCPServer, MCPServerConfig, create_mcp_server_for_agent
from contexa_sdk.mcp.server.protocol import MCPRequest


class TestTool(ContexaTool):
    """Test tool for integration testing."""
    
    def __init__(self):
        self.name = "test_calculator"
        self.description = "A simple calculator for testing"
        self.parameters_schema = {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                "a": {"type": "number"},
                "b": {"type": "number"}
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
        
        return f"{a} {operation} {b} = {result}"


class TestMCPServerIntegration:
    """Integration tests for MCP server with handlers."""
    
    @pytest.fixture
    async def server(self):
        """Create an MCP server for testing."""
        config = MCPServerConfig(
            name="Test MCP Server",
            version="1.0.0",
            description="Test server for integration testing",
            transport_type="stdio"  # Use stdio for testing
        )
        
        server = MCPServer(config)
        yield server
        
        if server.running:
            await server.stop()
    
    @pytest.fixture
    async def agent(self):
        """Create a test agent."""
        tool = TestTool()
        agent = ContexaAgent(
            name="Test Agent",
            description="A test agent for MCP integration",
            model=ContexaModel(model_name="gpt-4o", provider="openai"),
            tools=[tool]
        )
        return agent
    
    @pytest.mark.asyncio
    async def test_server_initialization(self, server):
        """Test server initialization with handlers."""
        # Check that handlers are created
        assert "resource" in server.handlers
        assert "tool" in server.handlers
        assert "prompt" in server.handlers
        assert "sampling" in server.handlers
        
        # Check server info
        info = server.get_server_info()
        assert info["name"] == "Test MCP Server"
        assert info["running"] is False
        assert info["initialized"] is False
    
    @pytest.mark.asyncio
    async def test_agent_registration(self, server, agent):
        """Test agent registration with handlers."""
        await server.register_agent(agent)
        
        # Check that agent is registered
        assert "Test Agent" in server.agents
        assert len(server.tools) == 1
        assert "test_calculator" in server.tools
        
        # Check that tool is registered with handler
        tool_handler = server.handlers["tool"]
        assert "test_calculator" in tool_handler.tools
    
    @pytest.mark.asyncio
    async def test_tool_operations(self, server, agent):
        """Test tool operations through handlers."""
        await server.register_agent(agent)
        
        # Test tool listing
        request = MCPRequest(method="tools/list", id="test_list")
        response = await server._handle_list_tools(request)
        
        assert "tools" in response
        assert len(response["tools"]) == 1
        assert response["tools"][0]["name"] == "test_calculator"
        
        # Test tool execution
        request = MCPRequest(
            method="tools/call",
            id="test_call",
            params={
                "name": "test_calculator",
                "arguments": {
                    "operation": "add",
                    "a": 5,
                    "b": 3
                }
            }
        )
        response = await server._handle_call_tool(request)
        
        assert "content" in response
        assert response["isError"] is False
        assert "5 add 3 = 8" in response["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_resource_operations(self, server):
        """Test resource operations through handlers."""
        # Initialize handlers first
        for handler in server.handlers.values():
            await handler.initialize()
        
        # Test resource listing
        request = MCPRequest(method="resources/list", id="test_list")
        response = await server._handle_list_resources(request)
        
        assert "resources" in response
        assert len(response["resources"]) >= 2  # Default resources
        
        # Find system info resource
        system_info = None
        for resource in response["resources"]:
            if resource["uri"] == "system://info":
                system_info = resource
                break
        
        assert system_info is not None
        assert system_info["name"] == "System Information"
        
        # Test resource reading
        request = MCPRequest(
            method="resources/read",
            id="test_read",
            params={"uri": "system://info"}
        )
        response = await server._handle_read_resource(request)
        
        assert "contents" in response
        assert len(response["contents"]) == 1
        
        # Parse the content
        content = json.loads(response["contents"][0]["text"])
        assert content["server_name"] == "Test MCP Server"
    
    @pytest.mark.asyncio
    async def test_prompt_operations(self, server):
        """Test prompt operations through handlers."""
        # Initialize handlers first
        for handler in server.handlers.values():
            await handler.initialize()
        
        # Test prompt listing
        request = MCPRequest(method="prompts/list", id="test_list")
        response = await server._handle_list_prompts(request)
        
        assert "prompts" in response
        assert len(response["prompts"]) >= 2  # Default prompts
        
        # Find system assistant prompt
        system_prompt = None
        for prompt in response["prompts"]:
            if prompt["name"] == "system_assistant":
                system_prompt = prompt
                break
        
        assert system_prompt is not None
        assert "arguments" in system_prompt
        
        # Test prompt rendering
        request = MCPRequest(
            method="prompts/get",
            id="test_get",
            params={
                "name": "system_assistant",
                "arguments": {
                    "task": "test task",
                    "context": "test context"
                }
            }
        )
        response = await server._handle_get_prompt(request)
        
        assert "messages" in response
        assert len(response["messages"]) == 1
        assert "test task" in response["messages"][0]["content"]["text"]
    
    @pytest.mark.asyncio
    async def test_sampling_operations(self, server):
        """Test sampling operations through handlers."""
        request = MCPRequest(
            method="sampling/createMessage",
            id="test_sampling",
            params={
                "messages": [
                    {"role": "user", "content": {"type": "text", "text": "Hello, world!"}}
                ],
                "systemPrompt": "You are a helpful assistant",
                "temperature": 0.7
            }
        )
        response = await server._handle_create_message(request)
        
        assert "role" in response
        assert response["role"] == "assistant"
        assert "content" in response
        assert "_meta" in response
        assert response["_meta"]["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_error_handling(self, server, agent):
        """Test error handling in integrated operations."""
        await server.register_agent(agent)
        
        # Test calling non-existent tool
        request = MCPRequest(
            method="tools/call",
            id="test_error",
            params={
                "name": "nonexistent_tool",
                "arguments": {}
            }
        )
        response = await server._handle_call_tool(request)
        
        assert response["isError"] is True
        assert "not found" in response["content"][0]["text"]
        
        # Test reading non-existent resource
        request = MCPRequest(
            method="resources/read",
            id="test_error",
            params={"uri": "nonexistent://resource"}
        )
        
        with pytest.raises(ValueError, match="Resource not found"):
            await server._handle_read_resource(request)
    
    @pytest.mark.asyncio
    async def test_convenience_function(self, agent):
        """Test the convenience function for creating servers."""
        server = await create_mcp_server_for_agent(agent, transport_type="stdio")
        
        try:
            # Check that agent is registered
            assert "Test Agent" in server.agents
            assert len(server.tools) == 1
            
            # Check server configuration
            assert server.config.name == "MCP Server for Test Agent"
            assert server.config.transport_type == "stdio"
            
            # Test that tools work
            request = MCPRequest(method="tools/list", id="test")
            response = await server._handle_list_tools(request)
            assert len(response["tools"]) == 1
            
        finally:
            if server.running:
                await server.stop()


if __name__ == "__main__":
    pytest.main([__file__]) 