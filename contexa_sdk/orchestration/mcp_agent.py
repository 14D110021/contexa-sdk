"""
MCP-Compatible Agent Interface for Contexa SDK.

This module provides a standardized MCP-based interface for agent-to-agent
communications, supporting both synchronous and asynchronous patterns.

Key Components:
---------------
1. MCPAgent: Core interface that standardizes agent communication
2. AgentManifest: Self-description of an agent's capabilities and interfaces
3. MessageEnvelope: Standardized container for inter-agent communications
4. Registry: Central registry for agent discovery and capability lookup
5. TaskBroker: Coordinates message routing and delivery between agents

Implementation Principles:
-------------------------
- Standardized Message Format: All communications use structured envelopes
- Capability-Based Discovery: Agents can be discovered by their capabilities
- Lifecycle Management: Agents have defined lifecycle states
- Back-Compatibility: Works with existing Contexa components 
- Runtime Discovery: Dynamically find available agents

This protocol is inspired by industry standards like IBM's Agent Communication
Protocol (ACP) and aligns with Anthropic's Model Context Protocol (MCP) principles.
"""

import uuid
import time
import json
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Callable, AsyncIterator
from pydantic import BaseModel, Field

# Agent Lifecycle States based on ACP specifications
class AgentState(str, Enum):
    """Agent lifecycle states"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    DEGRADED = "degraded"
    RETIRING = "retiring"
    RETIRED = "retired"

class AgentManifest(BaseModel):
    """Agent manifest describing capabilities and interface"""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Description of the agent's purpose and capabilities")
    version: str = Field(..., description="Version string for the agent")
    capabilities: List[str] = Field(default_factory=list, description="List of capability identifiers")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for input validation")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for output validation")
    accepts_streaming: bool = Field(False, description="Whether the agent can handle streaming input")
    produces_streaming: bool = Field(False, description="Whether the agent can produce streaming output")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional agent metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "agent_id": "research-agent-v1",
                "name": "Research Agent",
                "description": "Performs research on given topics and returns structured findings",
                "version": "1.0.0",
                "capabilities": ["research", "summarization", "citation-checking"],
                "accepts_streaming": False,
                "produces_streaming": True,
                "metadata": {
                    "creator": "Contexa",
                    "model": "gpt-4"
                }
            }
        }

class MessageEnvelope(BaseModel):
    """Standard message envelope for agent communications"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = Field(..., description="ID of the sending agent")
    recipient_id: str = Field(..., description="ID of the receiving agent")
    task_id: Optional[str] = Field(None, description="ID for tracking related messages in a task")
    timestamp: float = Field(default_factory=time.time)
    message_type: str = Field("request", description="Type of message (request, response, error, stream)")
    content: Dict[str, Any] = Field(..., description="Message content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "message_id": "msg-123e4567-e89b-12d3-a456-426614174000",
                "sender_id": "agent-orchestrator",
                "recipient_id": "agent-researcher",
                "task_id": "task-123e4567-e89b-12d3-a456-426614174000",
                "timestamp": 1682534400.123,
                "message_type": "request",
                "content": {
                    "query": "Research recent developments in quantum computing",
                    "max_results": 5
                },
                "metadata": {
                    "priority": "high",
                    "context": "technical-report"
                }
            }
        }

class MCPAgent:
    """MCP-compatible agent interface for standardized communications"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        version: str = "1.0.0",
        capabilities: List[str] = None,
        input_schema: Dict[str, Any] = None,
        output_schema: Dict[str, Any] = None,
        accepts_streaming: bool = False,
        produces_streaming: bool = False,
        metadata: Dict[str, Any] = None,
    ):
        """Initialize an MCP-compatible agent
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            description: Description of the agent's purpose
            version: Version string
            capabilities: List of capability identifiers
            input_schema: JSON Schema for input validation
            output_schema: JSON Schema for output validation
            accepts_streaming: Whether the agent can handle streaming input
            produces_streaming: Whether the agent can produce streaming output
            metadata: Additional agent metadata
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.version = version
        self.capabilities = capabilities or []
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.accepts_streaming = accepts_streaming
        self.produces_streaming = produces_streaming
        self.metadata = metadata or {}
        self.state = AgentState.INITIALIZING
        self._execution_handler = None
        self._stream_handler = None
        self._on_state_change_callbacks = []
        
    def get_manifest(self) -> AgentManifest:
        """Get the agent's capabilities manifest"""
        return AgentManifest(
            agent_id=self.agent_id,
            name=self.name,
            description=self.description,
            version=self.version,
            capabilities=self.capabilities,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            accepts_streaming=self.accepts_streaming,
            produces_streaming=self.produces_streaming,
            metadata=self.metadata
        )
    
    def set_execution_handler(self, handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """Set the function that handles requests to this agent
        
        Args:
            handler: Function that takes a message content dict and returns a result dict
        """
        self._execution_handler = handler
        return self
        
    def set_stream_handler(self, handler: Callable[[Dict[str, Any]], AsyncIterator[Dict[str, Any]]]):
        """Set the function that handles streaming requests to this agent
        
        Args:
            handler: Async function that takes a message content dict and yields result chunks
        """
        self._stream_handler = handler
        self.produces_streaming = True
        return self
    
    def on_state_change(self, callback: Callable[[AgentState, AgentState], None]):
        """Register a callback for agent state changes
        
        Args:
            callback: Function called with (old_state, new_state) when state changes
        """
        self._on_state_change_callbacks.append(callback)
        return self
    
    def set_state(self, state: AgentState):
        """Update the agent's lifecycle state
        
        Args:
            state: New agent state
        """
        old_state = self.state
        self.state = state
        
        # Notify all registered callbacks
        for callback in self._on_state_change_callbacks:
            callback(old_state, state)
        
        return self
        
    def process_message(self, message: MessageEnvelope) -> MessageEnvelope:
        """Process an incoming message and return a response
        
        Args:
            message: The incoming message envelope
            
        Returns:
            Response message envelope
            
        Raises:
            ValueError: If the agent cannot process the message
        """
        if not self._execution_handler:
            raise ValueError(f"Agent {self.agent_id} has no execution handler defined")
            
        if self.state != AgentState.ACTIVE:
            return MessageEnvelope(
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                task_id=message.task_id,
                message_type="error",
                content={
                    "error": f"Agent {self.agent_id} is not active (current state: {self.state})",
                    "code": "agent_not_active"
                }
            )
        
        try:
            # Process the message
            result = self._execution_handler(message.content)
            
            # Create response envelope
            return MessageEnvelope(
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                task_id=message.task_id,
                message_type="response",
                content=result
            )
        except Exception as e:
            # Handle errors
            return MessageEnvelope(
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                task_id=message.task_id,
                message_type="error",
                content={
                    "error": str(e),
                    "code": "execution_error"
                }
            )
    
    async def process_stream(self, message: MessageEnvelope) -> AsyncIterator[MessageEnvelope]:
        """Process a streaming request and yield response chunks
        
        Args:
            message: The incoming message envelope
            
        Yields:
            Response message envelopes with partial content
            
        Raises:
            ValueError: If the agent cannot handle streaming
        """
        if not self._stream_handler:
            raise ValueError(f"Agent {self.agent_id} has no stream handler defined")
            
        if not self.produces_streaming:
            raise ValueError(f"Agent {self.agent_id} does not support streaming output")
            
        if self.state != AgentState.ACTIVE:
            yield MessageEnvelope(
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                task_id=message.task_id,
                message_type="error",
                content={
                    "error": f"Agent {self.agent_id} is not active (current state: {self.state})",
                    "code": "agent_not_active"
                }
            )
            return
            
        try:
            # Process the message in streaming mode
            chunk_id = 0
            async for chunk in self._stream_handler(message.content):
                yield MessageEnvelope(
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    task_id=message.task_id,
                    message_type="stream",
                    content={
                        "chunk_id": chunk_id,
                        "is_last": False,
                        "data": chunk
                    }
                )
                chunk_id += 1
                
            # Send final message indicating stream completion
            yield MessageEnvelope(
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                task_id=message.task_id,
                message_type="stream",
                content={
                    "chunk_id": chunk_id,
                    "is_last": True,
                    "data": {}
                }
            )
        except Exception as e:
            # Handle errors
            yield MessageEnvelope(
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                task_id=message.task_id,
                message_type="error",
                content={
                    "error": str(e),
                    "code": "stream_execution_error"
                }
            )


class Registry:
    """Registry for MCP-compatible agents to enable discovery.
    
    The Registry serves as a central repository for agent discovery and capability lookup.
    It enables:
    
    1. Dynamic agent discovery at runtime based on capabilities
    2. Runtime agent replacement/update (hot-swapping)
    3. Inventory management of available agents
    4. Capability-based routing of requests
    
    Agents register themselves with the registry, making their capabilities
    available for discovery by other agents or orchestrators.
    
    Example:
        ```python
        # Register an agent
        registry.register(my_agent)
        
        # Find agents by capability
        research_agents = registry.find_by_capability("research")
        
        # Get a specific agent
        agent = registry.get_agent("agent-123")
        ```
    """
    
    def __init__(self):
        self.agents = {}
        
    def register(self, agent: MCPAgent):
        """Register an agent with the registry
        
        Args:
            agent: The agent to register
        """
        self.agents[agent.agent_id] = agent
        return self
        
    def unregister(self, agent_id: str):
        """Remove an agent from the registry
        
        Args:
            agent_id: ID of the agent to remove
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
        return self
        
    def get_agent(self, agent_id: str) -> Optional[MCPAgent]:
        """Get an agent by ID
        
        Args:
            agent_id: ID of the agent to retrieve
            
        Returns:
            The agent if found, None otherwise
        """
        return self.agents.get(agent_id)
        
    def list_agents(self) -> List[AgentManifest]:
        """List all registered agents
        
        Returns:
            List of agent manifests
        """
        return [agent.get_manifest() for agent in self.agents.values()]
        
    def find_by_capability(self, capability: str) -> List[AgentManifest]:
        """Find agents by capability
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of agent manifests with the requested capability
        """
        return [
            agent.get_manifest() for agent in self.agents.values()
            if capability in agent.capabilities
        ]


# Create a global registry instance
registry = Registry()


class TaskBroker:
    """Task broker for coordinating agent communications.
    
    The TaskBroker is responsible for handling the routing and delivery of messages
    between agents in the system. It provides:
    
    1. Message routing based on recipient ID
    2. Task creation and tracking
    3. Message history for debugging and auditing
    4. Support for both synchronous and streaming communications
    
    The broker maintains a record of all messages sent as part of each task,
    allowing for complete task history and potential replay or analysis.
    
    Example:
        ```python
        # Create a task
        task_id = broker.create_task()
        
        # Send a message
        response = broker.send_message(message)
        
        # Send a streaming message
        async for chunk in broker.send_streaming_message(message):
            process_chunk(chunk)
            
        # Get task history
        messages = broker.get_task_messages(task_id)
        ```
    """
    
    def __init__(self, registry: Registry):
        self.registry = registry
        self.tasks = {}
        
    def create_task(self, task_id: Optional[str] = None) -> str:
        """Create a new task for tracking related messages
        
        Args:
            task_id: Optional task ID (generated if not provided)
            
        Returns:
            Task ID
        """
        task_id = task_id or str(uuid.uuid4())
        self.tasks[task_id] = {
            "created_at": time.time(),
            "messages": [],
            "status": "created",
            "metadata": {}
        }
        return task_id
    
    def send_message(self, message: MessageEnvelope) -> Optional[MessageEnvelope]:
        """Send a message to an agent and get the response
        
        Args:
            message: Message to send
            
        Returns:
            Response message if synchronous, None if asynchronous
        """
        # Track the task if it has a task_id
        if message.task_id:
            if message.task_id not in self.tasks:
                self.create_task(message.task_id)
            self.tasks[message.task_id]["messages"].append(message)
            
        # Get the recipient agent
        recipient = self.registry.get_agent(message.recipient_id)
        if not recipient:
            raise ValueError(f"Agent {message.recipient_id} not found in registry")
            
        # Process the message
        response = recipient.process_message(message)
        
        # Store the response in the task
        if message.task_id:
            self.tasks[message.task_id]["messages"].append(response)
            
        return response
    
    async def send_streaming_message(self, message: MessageEnvelope) -> AsyncIterator[MessageEnvelope]:
        """Send a message to an agent and stream the response
        
        Args:
            message: Message to send
            
        Yields:
            Response message chunks
        """
        # Track the task if it has a task_id
        if message.task_id:
            if message.task_id not in self.tasks:
                self.create_task(message.task_id)
            self.tasks[message.task_id]["messages"].append(message)
            
        # Get the recipient agent
        recipient = self.registry.get_agent(message.recipient_id)
        if not recipient:
            raise ValueError(f"Agent {message.recipient_id} not found in registry")
            
        # Process the message with streaming
        async for response in recipient.process_stream(message):
            # Store the response chunks in the task
            if message.task_id:
                self.tasks[message.task_id]["messages"].append(response)
                
            yield response
    
    def get_task_messages(self, task_id: str) -> List[MessageEnvelope]:
        """Get all messages for a task
        
        Args:
            task_id: ID of the task
            
        Returns:
            List of messages in the task
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
            
        return self.tasks[task_id]["messages"]


# Create a global task broker instance
broker = TaskBroker(registry) 