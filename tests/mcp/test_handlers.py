"""
Unit tests for MCP handlers.

This module tests all MCP feature handlers including ResourceHandler,
ToolHandler, PromptHandler, and SamplingHandler.
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from contexa_sdk.mcp.server.handlers import (
    ResourceHandler, ToolHandler, PromptHandler, SamplingHandler,
    MCPResource, MCPPromptTemplate, create_handlers
)
from contexa_sdk.core.tool import ContexaTool


class MockTool(ContexaTool):
    """Mock tool for testing."""
    
    def __init__(self, name: str, description: str = None):
        self.name = name
        self.description = description or f"Mock tool: {name}"
        self.parameters_schema = {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input parameter"}
            },
            "required": ["input"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute the mock tool."""
        input_value = arguments.get("input", "")
        return f"Mock result for: {input_value}"


class TestResourceHandler:
    """Test cases for ResourceHandler."""
    
    @pytest.fixture
    async def handler(self):
        """Create a ResourceHandler for testing."""
        config = {"name": "Test Server", "version": "1.0.0"}
        handler = ResourceHandler(config)
        await handler.initialize()
        yield handler
        await handler.cleanup()
    
    @pytest.mark.asyncio
    async def test_initialization(self, handler):
        """Test handler initialization."""
        assert len(handler.resources) >= 2  # Default resources
        assert "system://info" in handler.resources
        assert "system://status" in handler.resources
    
    @pytest.mark.asyncio
    async def test_register_resource(self, handler):
        """Test resource registration."""
        resource = MCPResource(
            uri="test://resource",
            name="Test Resource",
            description="A test resource",
            mime_type="text/plain"
        )
        
        await handler.register_resource(resource, content="Test content")
        
        assert resource.uri in handler.resources
        assert handler.resource_content[resource.uri] == "Test content"
    
    @pytest.mark.asyncio
    async def test_list_resources(self, handler):
        """Test resource listing."""
        resources = await handler.list_resources()
        
        assert isinstance(resources, list)
        assert len(resources) >= 2
        
        # Check resource structure
        for resource in resources:
            assert "uri" in resource
            assert "name" in resource
    
    @pytest.mark.asyncio
    async def test_read_resource(self, handler):
        """Test resource reading."""
        # Test reading system info
        result = await handler.read_resource("system://info")
        
        assert "contents" in result
        assert len(result["contents"]) == 1
        assert "uri" in result["contents"][0]
        assert "text" in result["contents"][0]
        
        # Parse the JSON content
        content = json.loads(result["contents"][0]["text"])
        assert "server_name" in content
        assert content["server_name"] == "Test Server"
    
    @pytest.mark.asyncio
    async def test_read_nonexistent_resource(self, handler):
        """Test reading a non-existent resource."""
        with pytest.raises(ValueError, match="Resource not found"):
            await handler.read_resource("nonexistent://resource")
    
    @pytest.mark.asyncio
    async def test_resource_subscriptions(self, handler):
        """Test resource subscriptions."""
        client_id = "test_client"
        uri = "system://info"
        
        # Subscribe to resource
        await handler.subscribe_to_resource(client_id, uri)
        assert client_id in handler.subscriptions
        assert uri in handler.subscriptions[client_id]
        
        # Unsubscribe from resource
        await handler.unsubscribe_from_resource(client_id, uri)
        assert client_id not in handler.subscriptions
    
    @pytest.mark.asyncio
    async def test_update_resource_content(self, handler):
        """Test updating resource content."""
        # Register a test resource
        resource = MCPResource(uri="test://update", name="Update Test")
        await handler.register_resource(resource, content="Original content")
        
        # Update content
        new_content = "Updated content"
        await handler.update_resource_content(resource.uri, new_content)
        
        assert handler.resource_content[resource.uri] == new_content


class TestToolHandler:
    """Test cases for ToolHandler."""
    
    @pytest.fixture
    async def handler(self):
        """Create a ToolHandler for testing."""
        handler = ToolHandler()
        await handler.initialize()
        yield handler
        await handler.cleanup()
    
    @pytest.fixture
    def mock_tool(self):
        """Create a mock tool for testing."""
        return MockTool("test_tool", "A test tool")
    
    @pytest.mark.asyncio
    async def test_initialization(self, handler):
        """Test handler initialization."""
        assert len(handler.tools) == 0
        assert len(handler.execution_history) == 0
    
    @pytest.mark.asyncio
    async def test_register_tool(self, handler, mock_tool):
        """Test tool registration."""
        await handler.register_tool(mock_tool)
        
        assert mock_tool.name in handler.tools
        assert handler.tools[mock_tool.name] == mock_tool
    
    @pytest.mark.asyncio
    async def test_list_tools(self, handler, mock_tool):
        """Test tool listing."""
        await handler.register_tool(mock_tool)
        tools = await handler.list_tools()
        
        assert isinstance(tools, list)
        assert len(tools) == 1
        
        tool_dict = tools[0]
        assert tool_dict["name"] == mock_tool.name
        assert tool_dict["description"] == mock_tool.description
        assert "inputSchema" in tool_dict
    
    @pytest.mark.asyncio
    async def test_call_tool(self, handler, mock_tool):
        """Test tool execution."""
        await handler.register_tool(mock_tool)
        
        arguments = {"input": "test input"}
        result = await handler.call_tool(mock_tool.name, arguments)
        
        assert "content" in result
        assert "isError" in result
        assert result["isError"] is False
        assert "_meta" in result
        
        # Check execution history
        assert len(handler.execution_history) == 1
        execution = handler.execution_history[0]
        assert execution["tool_name"] == mock_tool.name
        assert execution["arguments"] == arguments
    
    @pytest.mark.asyncio
    async def test_call_nonexistent_tool(self, handler):
        """Test calling a non-existent tool."""
        result = await handler.call_tool("nonexistent_tool", {})
        
        assert result["isError"] is True
        assert "Error executing tool" in result["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_tool_validation(self, handler, mock_tool):
        """Test tool argument validation."""
        await handler.register_tool(mock_tool)
        
        # Test missing required parameter
        result = await handler.call_tool(mock_tool.name, {})
        assert result["isError"] is True
    
    @pytest.mark.asyncio
    async def test_execution_history(self, handler, mock_tool):
        """Test execution history tracking."""
        await handler.register_tool(mock_tool)
        
        # Execute tool multiple times
        for i in range(3):
            await handler.call_tool(mock_tool.name, {"input": f"test {i}"})
        
        history = handler.get_execution_history()
        assert len(history) == 3
        
        # Test limited history
        limited_history = handler.get_execution_history(limit=2)
        assert len(limited_history) == 2


class TestPromptHandler:
    """Test cases for PromptHandler."""
    
    @pytest.fixture
    async def handler(self):
        """Create a PromptHandler for testing."""
        handler = PromptHandler()
        await handler.initialize()
        yield handler
        await handler.cleanup()
    
    @pytest.mark.asyncio
    async def test_initialization(self, handler):
        """Test handler initialization."""
        assert len(handler.prompts) >= 2  # Default prompts
        assert "system_assistant" in handler.prompts
        assert "error_handler" in handler.prompts
    
    @pytest.mark.asyncio
    async def test_register_prompt(self, handler):
        """Test prompt registration."""
        prompt = MCPPromptTemplate(
            name="test_prompt",
            description="A test prompt",
            arguments=[
                {"name": "param1", "description": "Parameter 1", "required": True}
            ]
        )
        content = "Test prompt with {param1}"
        
        await handler.register_prompt(prompt, content=content)
        
        assert prompt.name in handler.prompts
        assert handler.prompt_content[prompt.name] == content
    
    @pytest.mark.asyncio
    async def test_list_prompts(self, handler):
        """Test prompt listing."""
        prompts = await handler.list_prompts()
        
        assert isinstance(prompts, list)
        assert len(prompts) >= 2
        
        # Check prompt structure
        for prompt in prompts:
            assert "name" in prompt
    
    @pytest.mark.asyncio
    async def test_get_prompt(self, handler):
        """Test prompt rendering."""
        arguments = {"task": "test task", "context": "test context"}
        result = await handler.get_prompt("system_assistant", arguments)
        
        assert "description" in result
        assert "messages" in result
        assert len(result["messages"]) == 1
        
        message = result["messages"][0]
        assert message["role"] == "user"
        assert "content" in message
        assert "test task" in message["content"]["text"]
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_prompt(self, handler):
        """Test getting a non-existent prompt."""
        with pytest.raises(ValueError, match="Prompt 'nonexistent' not found"):
            await handler.get_prompt("nonexistent")
    
    @pytest.mark.asyncio
    async def test_prompt_validation(self, handler):
        """Test prompt argument validation."""
        # Test missing required argument
        with pytest.raises(ValueError, match="Missing required argument"):
            await handler.get_prompt("system_assistant", {})


class TestSamplingHandler:
    """Test cases for SamplingHandler."""
    
    @pytest.fixture
    async def handler(self):
        """Create a SamplingHandler for testing."""
        handler = SamplingHandler()
        await handler.initialize()
        yield handler
        await handler.cleanup()
    
    @pytest.mark.asyncio
    async def test_initialization(self, handler):
        """Test handler initialization."""
        assert len(handler.sampling_history) == 0
        assert "costPriority" in handler.default_model_preferences
    
    @pytest.mark.asyncio
    async def test_create_message(self, handler):
        """Test message creation."""
        messages = [
            {"role": "user", "content": {"type": "text", "text": "Hello"}}
        ]
        
        result = await handler.create_message(messages)
        
        assert "role" in result
        assert result["role"] == "assistant"
        assert "content" in result
        assert "_meta" in result
        
        # Check sampling history
        assert len(handler.sampling_history) == 1
    
    @pytest.mark.asyncio
    async def test_create_message_with_preferences(self, handler):
        """Test message creation with model preferences."""
        messages = [
            {"role": "user", "content": {"type": "text", "text": "Hello"}}
        ]
        preferences = {"costPriority": 0.8}
        
        result = await handler.create_message(messages, model_preferences=preferences)
        
        assert result["_meta"]["preferences"]["costPriority"] == 0.8
    
    @pytest.mark.asyncio
    async def test_create_message_with_system_prompt(self, handler):
        """Test message creation with system prompt."""
        messages = [
            {"role": "user", "content": {"type": "text", "text": "Hello"}}
        ]
        system_prompt = "You are a helpful assistant"
        
        result = await handler.create_message(messages, system_prompt=system_prompt)
        
        assert system_prompt in result["content"]["text"]
    
    @pytest.mark.asyncio
    async def test_invalid_messages(self, handler):
        """Test handling of invalid messages."""
        # Empty messages
        result = await handler.create_message([])
        assert "Error during sampling" in result["content"]["text"]
        
        # Invalid message format
        invalid_messages = [{"invalid": "message"}]
        result = await handler.create_message(invalid_messages)
        assert "Error during sampling" in result["content"]["text"]
    
    @pytest.mark.asyncio
    async def test_sampling_history(self, handler):
        """Test sampling history tracking."""
        messages = [
            {"role": "user", "content": {"type": "text", "text": "Hello"}}
        ]
        
        # Create multiple sampling requests
        for i in range(3):
            await handler.create_message(messages)
        
        history = handler.get_sampling_history()
        assert len(history) == 3
        
        # Test limited history
        limited_history = handler.get_sampling_history(limit=2)
        assert len(limited_history) == 2


class TestHandlerFactory:
    """Test cases for handler factory function."""
    
    def test_create_handlers(self):
        """Test handler factory function."""
        config = {"name": "Test Server"}
        handlers = create_handlers(config)
        
        assert "resource" in handlers
        assert "tool" in handlers
        assert "prompt" in handlers
        assert "sampling" in handlers
        
        assert isinstance(handlers["resource"], ResourceHandler)
        assert isinstance(handlers["tool"], ToolHandler)
        assert isinstance(handlers["prompt"], PromptHandler)
        assert isinstance(handlers["sampling"], SamplingHandler)


if __name__ == "__main__":
    pytest.main([__file__]) 