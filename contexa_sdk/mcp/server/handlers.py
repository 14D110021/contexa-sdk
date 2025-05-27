"""
MCP Feature Handlers for specialized MCP capabilities.

This module provides specialized handlers for each MCP feature type:
- ResourceHandler: Resource management and subscriptions
- ToolHandler: Tool execution and management
- PromptHandler: Prompt templates and workflows
- SamplingHandler: LLM sampling requests

Each handler implements the MCP specification requirements and integrates
with the Contexa SDK agent system.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
import time
from pathlib import Path

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.prompt import ContexaPrompt

logger = logging.getLogger(__name__)


@dataclass
class MCPResource:
    """Represents an MCP resource."""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    annotations: Optional[Dict[str, Any]] = None


@dataclass
class MCPPromptTemplate:
    """Represents an MCP prompt template."""
    name: str
    description: Optional[str] = None
    arguments: Optional[List[Dict[str, Any]]] = None


class MCPHandler(ABC):
    """Base class for MCP feature handlers."""
    
    def __init__(self, server_config: Optional[Dict[str, Any]] = None):
        self.config = server_config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def initialize(self):
        """Initialize the handler."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Clean up handler resources."""
        pass


class ResourceHandler(MCPHandler):
    """
    Handler for MCP resource management and subscriptions.
    
    This handler manages resources that can be read by MCP clients,
    supports resource subscriptions for change notifications, and
    provides resource discovery capabilities.
    """
    
    def __init__(self, server_config: Optional[Dict[str, Any]] = None):
        super().__init__(server_config)
        self.resources: Dict[str, MCPResource] = {}
        self.resource_content: Dict[str, Any] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of resource URIs
        self.change_callbacks: List[Callable[[str], None]] = []
        
    async def initialize(self):
        """Initialize the resource handler."""
        self.logger.info("Initializing ResourceHandler")
        
        # Register default resources
        await self._register_default_resources()
        
        self.logger.info(f"ResourceHandler initialized with {len(self.resources)} resources")
    
    async def cleanup(self):
        """Clean up resource handler."""
        self.logger.info("Cleaning up ResourceHandler")
        self.subscriptions.clear()
        self.change_callbacks.clear()
    
    async def _register_default_resources(self):
        """Register default system resources."""
        # System information resource
        await self.register_resource(
            MCPResource(
                uri="system://info",
                name="System Information",
                description="Current system and server information",
                mime_type="application/json"
            ),
            content={
                "server_name": self.config.get("name", "Contexa MCP Server"),
                "server_version": self.config.get("version", "1.0.0"),
                "timestamp": time.time(),
                "capabilities": ["resources", "tools", "prompts"]
            }
        )
        
        # Server status resource
        await self.register_resource(
            MCPResource(
                uri="system://status",
                name="Server Status",
                description="Current server status and metrics",
                mime_type="application/json"
            ),
            content={
                "status": "running",
                "uptime": 0,
                "resource_count": 0,
                "subscription_count": 0
            }
        )
    
    async def register_resource(self, resource: MCPResource, content: Any = None):
        """Register a new resource."""
        self.resources[resource.uri] = resource
        if content is not None:
            self.resource_content[resource.uri] = content
        
        self.logger.debug(f"Registered resource: {resource.uri}")
        
        # Notify subscribers of new resource
        await self._notify_resource_change(resource.uri, "created")
    
    async def unregister_resource(self, uri: str):
        """Unregister a resource."""
        if uri in self.resources:
            del self.resources[uri]
            self.resource_content.pop(uri, None)
            
            self.logger.debug(f"Unregistered resource: {uri}")
            
            # Notify subscribers of resource removal
            await self._notify_resource_change(uri, "deleted")
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources."""
        resources = []
        for resource in self.resources.values():
            resource_dict = {
                "uri": resource.uri,
                "name": resource.name,
            }
            if resource.description:
                resource_dict["description"] = resource.description
            if resource.mime_type:
                resource_dict["mimeType"] = resource.mime_type
            if resource.annotations:
                resource_dict["annotations"] = resource.annotations
            
            resources.append(resource_dict)
        
        self.logger.debug(f"Listed {len(resources)} resources")
        return resources
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific resource."""
        if uri not in self.resources:
            raise ValueError(f"Resource not found: {uri}")
        
        resource = self.resources[uri]
        content = self.resource_content.get(uri)
        
        # Update dynamic resources
        if uri == "system://status":
            content = await self._get_server_status()
        
        result = {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": resource.mime_type or "text/plain",
                }
            ]
        }
        
        if content is not None:
            if isinstance(content, (dict, list)):
                result["contents"][0]["text"] = json.dumps(content, indent=2)
            else:
                result["contents"][0]["text"] = str(content)
        
        self.logger.debug(f"Read resource: {uri}")
        return result
    
    async def subscribe_to_resource(self, client_id: str, uri: str):
        """Subscribe a client to resource changes."""
        if uri not in self.resources:
            raise ValueError(f"Resource not found: {uri}")
        
        if client_id not in self.subscriptions:
            self.subscriptions[client_id] = set()
        
        self.subscriptions[client_id].add(uri)
        self.logger.debug(f"Client {client_id} subscribed to resource: {uri}")
    
    async def unsubscribe_from_resource(self, client_id: str, uri: str):
        """Unsubscribe a client from resource changes."""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].discard(uri)
            if not self.subscriptions[client_id]:
                del self.subscriptions[client_id]
        
        self.logger.debug(f"Client {client_id} unsubscribed from resource: {uri}")
    
    async def update_resource_content(self, uri: str, content: Any):
        """Update the content of a resource."""
        if uri not in self.resources:
            raise ValueError(f"Resource not found: {uri}")
        
        self.resource_content[uri] = content
        await self._notify_resource_change(uri, "updated")
        
        self.logger.debug(f"Updated resource content: {uri}")
    
    async def _notify_resource_change(self, uri: str, change_type: str):
        """Notify subscribers of resource changes."""
        # Find all clients subscribed to this resource
        notified_clients = []
        for client_id, subscribed_uris in self.subscriptions.items():
            if uri in subscribed_uris:
                notified_clients.append(client_id)
        
        if notified_clients:
            self.logger.debug(f"Notifying {len(notified_clients)} clients of {change_type} for resource: {uri}")
        
        # Call registered change callbacks
        for callback in self.change_callbacks:
            try:
                await callback(uri)
            except Exception as e:
                self.logger.error(f"Error in resource change callback: {e}")
    
    async def _get_server_status(self) -> Dict[str, Any]:
        """Get current server status."""
        return {
            "status": "running",
            "uptime": time.time(),
            "resource_count": len(self.resources),
            "subscription_count": sum(len(subs) for subs in self.subscriptions.values()),
            "timestamp": time.time()
        }
    
    def add_change_callback(self, callback: Callable[[str], None]):
        """Add a callback for resource changes."""
        self.change_callbacks.append(callback)


class ToolHandler(MCPHandler):
    """
    Handler for MCP tool execution and management.
    
    This handler manages tool registration, validation, execution,
    and result formatting according to MCP specifications.
    """
    
    def __init__(self, server_config: Optional[Dict[str, Any]] = None):
        super().__init__(server_config)
        self.tools: Dict[str, ContexaTool] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
    async def initialize(self):
        """Initialize the tool handler."""
        self.logger.info("Initializing ToolHandler")
        self.logger.info(f"ToolHandler initialized with {len(self.tools)} tools")
    
    async def cleanup(self):
        """Clean up tool handler."""
        self.logger.info("Cleaning up ToolHandler")
        self.execution_history.clear()
    
    async def register_tool(self, tool: ContexaTool, metadata: Optional[Dict[str, Any]] = None):
        """Register a tool with the handler."""
        self.tools[tool.name] = tool
        self.tool_metadata[tool.name] = metadata or {}
        
        self.logger.debug(f"Registered tool: {tool.name}")
    
    async def unregister_tool(self, tool_name: str):
        """Unregister a tool."""
        if tool_name in self.tools:
            del self.tools[tool_name]
            self.tool_metadata.pop(tool_name, None)
            
            self.logger.debug(f"Unregistered tool: {tool_name}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        tools = []
        for tool_name, tool in self.tools.items():
            tool_dict = {
                "name": tool.name,
                "description": tool.description or f"Tool: {tool.name}",
            }
            
            # Add input schema if available
            if hasattr(tool, 'parameters_schema'):
                tool_dict["inputSchema"] = tool.parameters_schema
            elif hasattr(tool, 'input_schema'):
                tool_dict["inputSchema"] = tool.input_schema
            else:
                # Create basic schema
                tool_dict["inputSchema"] = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            
            # Add metadata
            metadata = self.tool_metadata.get(tool_name, {})
            if metadata:
                tool_dict.update(metadata)
            
            tools.append(tool_dict)
        
        self.logger.debug(f"Listed {len(tools)} tools")
        return tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with the given arguments."""
        if name not in self.tools:
            return await self._format_tool_error(f"Tool '{name}' not found", 0.0)
        
        tool = self.tools[name]
        execution_id = f"{name}_{int(time.time() * 1000)}"
        
        start_time = time.time()
        
        try:
            self.logger.debug(f"Executing tool: {name} with arguments: {arguments}")
            
            # Validate arguments if schema is available
            await self._validate_tool_arguments(tool, arguments)
            
            # Execute the tool
            if hasattr(tool, 'execute'):
                result = await tool.execute(arguments)
            elif hasattr(tool, '__call__'):
                result = await tool(**arguments)
            else:
                raise ValueError(f"Tool '{name}' is not executable")
            
            execution_time = time.time() - start_time
            
            # Format result according to MCP specification
            formatted_result = await self._format_tool_result(result, execution_time)
            
            # Record execution history
            await self._record_execution(execution_id, name, arguments, formatted_result, execution_time, None)
            
            self.logger.debug(f"Tool execution completed: {name} in {execution_time:.3f}s")
            return formatted_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = await self._format_tool_error(str(e), execution_time)
            
            # Record execution history with error
            await self._record_execution(execution_id, name, arguments, error_result, execution_time, str(e))
            
            self.logger.error(f"Tool execution failed: {name} - {str(e)}")
            return error_result
    
    async def _validate_tool_arguments(self, tool: ContexaTool, arguments: Dict[str, Any]):
        """Validate tool arguments against schema."""
        # Basic validation - can be enhanced with jsonschema
        if hasattr(tool, 'parameters_schema'):
            schema = tool.parameters_schema
            required = schema.get('required', [])
            
            # Check required parameters
            for param in required:
                if param not in arguments:
                    raise ValueError(f"Missing required parameter: {param}")
    
    async def _format_tool_result(self, result: Any, execution_time: float) -> Dict[str, Any]:
        """Format tool result according to MCP specification."""
        content = []
        
        if isinstance(result, str):
            content.append({
                "type": "text",
                "text": result
            })
        elif isinstance(result, (dict, list)):
            content.append({
                "type": "text",
                "text": json.dumps(result, indent=2)
            })
        else:
            content.append({
                "type": "text",
                "text": str(result)
            })
        
        return {
            "content": content,
            "isError": False,
            "_meta": {
                "executionTime": execution_time,
                "timestamp": time.time()
            }
        }
    
    async def _format_tool_error(self, error: str, execution_time: float) -> Dict[str, Any]:
        """Format tool error according to MCP specification."""
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error executing tool: {error}"
                }
            ],
            "isError": True,
            "_meta": {
                "executionTime": execution_time,
                "timestamp": time.time(),
                "error": error
            }
        }
    
    async def _record_execution(self, execution_id: str, tool_name: str, arguments: Dict[str, Any], 
                               result: Dict[str, Any], execution_time: float, error: Optional[str]):
        """Record tool execution in history."""
        execution_record = {
            "id": execution_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "execution_time": execution_time,
            "timestamp": time.time(),
            "error": error
        }
        
        self.execution_history.append(execution_record)
        
        # Trim history if it gets too large
        if len(self.execution_history) > self.max_history_size:
            self.execution_history = self.execution_history[-self.max_history_size:]
    
    def get_execution_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get tool execution history."""
        if limit:
            return self.execution_history[-limit:]
        return self.execution_history.copy()


class PromptHandler(MCPHandler):
    """
    Handler for MCP prompt templates and workflows.
    
    This handler manages prompt templates, parameter validation,
    and prompt rendering according to MCP specifications.
    """
    
    def __init__(self, server_config: Optional[Dict[str, Any]] = None):
        super().__init__(server_config)
        self.prompts: Dict[str, MCPPromptTemplate] = {}
        self.prompt_content: Dict[str, str] = {}
        self.prompt_functions: Dict[str, Callable] = {}
        
    async def initialize(self):
        """Initialize the prompt handler."""
        self.logger.info("Initializing PromptHandler")
        
        # Register default prompts
        await self._register_default_prompts()
        
        self.logger.info(f"PromptHandler initialized with {len(self.prompts)} prompts")
    
    async def cleanup(self):
        """Clean up prompt handler."""
        self.logger.info("Cleaning up PromptHandler")
    
    async def _register_default_prompts(self):
        """Register default system prompts."""
        # System prompt for general assistance
        await self.register_prompt(
            MCPPromptTemplate(
                name="system_assistant",
                description="General system assistant prompt",
                arguments=[
                    {"name": "task", "description": "The task to perform", "required": True},
                    {"name": "context", "description": "Additional context", "required": False}
                ]
            ),
            content="You are a helpful assistant. Please help with the following task: {task}\n\nContext: {context}"
        )
        
        # Error handling prompt
        await self.register_prompt(
            MCPPromptTemplate(
                name="error_handler",
                description="Prompt for handling errors gracefully",
                arguments=[
                    {"name": "error", "description": "The error that occurred", "required": True},
                    {"name": "operation", "description": "The operation that failed", "required": True}
                ]
            ),
            content="An error occurred during {operation}: {error}\n\nPlease provide a helpful response to the user explaining what went wrong and how to resolve it."
        )
    
    async def register_prompt(self, prompt: MCPPromptTemplate, content: str = None, 
                            function: Callable = None):
        """Register a prompt template."""
        self.prompts[prompt.name] = prompt
        
        if content:
            self.prompt_content[prompt.name] = content
        
        if function:
            self.prompt_functions[prompt.name] = function
        
        self.logger.debug(f"Registered prompt: {prompt.name}")
    
    async def unregister_prompt(self, name: str):
        """Unregister a prompt template."""
        if name in self.prompts:
            del self.prompts[name]
            self.prompt_content.pop(name, None)
            self.prompt_functions.pop(name, None)
            
            self.logger.debug(f"Unregistered prompt: {name}")
    
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """List all available prompt templates."""
        prompts = []
        for prompt in self.prompts.values():
            prompt_dict = {
                "name": prompt.name,
            }
            if prompt.description:
                prompt_dict["description"] = prompt.description
            if prompt.arguments:
                prompt_dict["arguments"] = prompt.arguments
            
            prompts.append(prompt_dict)
        
        self.logger.debug(f"Listed {len(prompts)} prompts")
        return prompts
    
    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get and render a prompt template."""
        if name not in self.prompts:
            raise ValueError(f"Prompt '{name}' not found")
        
        prompt = self.prompts[name]
        arguments = arguments or {}
        
        # Validate arguments
        await self._validate_prompt_arguments(prompt, arguments)
        
        # Render prompt
        if name in self.prompt_functions:
            # Use function to generate prompt
            function = self.prompt_functions[name]
            rendered_content = await function(**arguments)
        elif name in self.prompt_content:
            # Use template string
            template = self.prompt_content[name]
            rendered_content = template.format(**arguments)
        else:
            rendered_content = f"Prompt: {name}"
        
        result = {
            "description": prompt.description or f"Prompt: {name}",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": rendered_content
                    }
                }
            ]
        }
        
        self.logger.debug(f"Rendered prompt: {name}")
        return result
    
    async def _validate_prompt_arguments(self, prompt: MCPPromptTemplate, arguments: Dict[str, Any]):
        """Validate prompt arguments."""
        if not prompt.arguments:
            return
        
        required_args = [arg["name"] for arg in prompt.arguments if arg.get("required", False)]
        
        for arg_name in required_args:
            if arg_name not in arguments:
                raise ValueError(f"Missing required argument: {arg_name}")


class SamplingHandler(MCPHandler):
    """
    Handler for MCP LLM sampling requests.
    
    This handler processes sampling requests, manages model preferences,
    and formats responses according to MCP specifications.
    """
    
    def __init__(self, server_config: Optional[Dict[str, Any]] = None):
        super().__init__(server_config)
        self.default_model_preferences = {
            "costPriority": 0.5,
            "speedPriority": 0.5,
            "intelligencePriority": 0.5
        }
        self.sampling_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
        
    async def initialize(self):
        """Initialize the sampling handler."""
        self.logger.info("Initializing SamplingHandler")
        self.logger.info("SamplingHandler initialized")
    
    async def cleanup(self):
        """Clean up sampling handler."""
        self.logger.info("Cleaning up SamplingHandler")
        self.sampling_history.clear()
    
    async def create_message(self, messages: List[Dict[str, Any]], 
                           model_preferences: Optional[Dict[str, Any]] = None,
                           system_prompt: Optional[str] = None,
                           include_context: str = "none",
                           temperature: Optional[float] = None,
                           max_tokens: Optional[int] = None,
                           stop_sequences: Optional[List[str]] = None) -> Dict[str, Any]:
        """Process a sampling request."""
        sampling_id = f"sampling_{int(time.time() * 1000)}"
        start_time = time.time()
        
        try:
            # Merge model preferences
            preferences = {**self.default_model_preferences}
            if model_preferences:
                preferences.update(model_preferences)
            
            # Validate messages
            await self._validate_messages(messages)
            
            # Process the sampling request
            result = await self._process_sampling(
                messages, preferences, system_prompt, include_context,
                temperature, max_tokens, stop_sequences
            )
            
            processing_time = time.time() - start_time
            
            # Record sampling history
            await self._record_sampling(sampling_id, messages, preferences, result, processing_time, None)
            
            self.logger.debug(f"Sampling completed: {sampling_id} in {processing_time:.3f}s")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_result = await self._format_sampling_error(str(e))
            
            # Record sampling history with error
            await self._record_sampling(sampling_id, messages, model_preferences, error_result, processing_time, str(e))
            
            self.logger.error(f"Sampling failed: {sampling_id} - {str(e)}")
            return error_result
    
    async def _validate_messages(self, messages: List[Dict[str, Any]]):
        """Validate message format."""
        if not messages:
            raise ValueError("Messages cannot be empty")
        
        for i, message in enumerate(messages):
            if "role" not in message:
                raise ValueError(f"Message {i} missing 'role' field")
            if "content" not in message:
                raise ValueError(f"Message {i} missing 'content' field")
    
    async def _process_sampling(self, messages: List[Dict[str, Any]], 
                              preferences: Dict[str, Any],
                              system_prompt: Optional[str],
                              include_context: str,
                              temperature: Optional[float],
                              max_tokens: Optional[int],
                              stop_sequences: Optional[List[str]]) -> Dict[str, Any]:
        """Process the actual sampling request."""
        # This is a mock implementation - in a real scenario, this would
        # interface with actual LLM APIs based on preferences
        
        # Simulate processing
        await asyncio.sleep(0.1)
        
        # Create a mock response
        last_message = messages[-1] if messages else {"content": {"text": ""}}
        last_content = last_message.get("content", {})
        
        if isinstance(last_content, str):
            prompt_text = last_content
        elif isinstance(last_content, dict):
            prompt_text = last_content.get("text", "")
        else:
            prompt_text = str(last_content)
        
        # Generate a simple response
        response_text = f"This is a mock response to: {prompt_text[:100]}..."
        
        if system_prompt:
            response_text = f"[System: {system_prompt}] {response_text}"
        
        return {
            "role": "assistant",
            "content": {
                "type": "text",
                "text": response_text
            },
            "_meta": {
                "model": "mock-model",
                "preferences": preferences,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stop_sequences": stop_sequences,
                "include_context": include_context,
                "timestamp": time.time()
            }
        }
    
    async def _format_sampling_error(self, error: str) -> Dict[str, Any]:
        """Format sampling error response."""
        return {
            "role": "assistant",
            "content": {
                "type": "text",
                "text": f"Error during sampling: {error}"
            },
            "_meta": {
                "error": error,
                "timestamp": time.time()
            }
        }
    
    async def _record_sampling(self, sampling_id: str, messages: List[Dict[str, Any]], 
                             preferences: Optional[Dict[str, Any]], result: Dict[str, Any], 
                             processing_time: float, error: Optional[str]):
        """Record sampling request in history."""
        sampling_record = {
            "id": sampling_id,
            "messages": messages,
            "preferences": preferences,
            "result": result,
            "processing_time": processing_time,
            "timestamp": time.time(),
            "error": error
        }
        
        self.sampling_history.append(sampling_record)
        
        # Trim history if it gets too large
        if len(self.sampling_history) > self.max_history_size:
            self.sampling_history = self.sampling_history[-self.max_history_size:]
    
    def get_sampling_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get sampling request history."""
        if limit:
            return self.sampling_history[-limit:]
        return self.sampling_history.copy()


# Factory function for creating handlers
def create_handlers(server_config: Optional[Dict[str, Any]] = None) -> Dict[str, MCPHandler]:
    """Create all MCP handlers."""
    return {
        "resource": ResourceHandler(server_config),
        "tool": ToolHandler(server_config),
        "prompt": PromptHandler(server_config),
        "sampling": SamplingHandler(server_config)
    } 