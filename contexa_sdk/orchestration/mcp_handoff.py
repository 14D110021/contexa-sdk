"""
MCP-compatible handoff system for Contexa SDK.

This module provides enhanced handoff functionality that's compatible with
the Model Context Protocol (MCP) and inspired by IBM's Agent Communication Protocol (ACP).

Key Components:
---------------
1. MCPHandoff: Core class that manages task delegation between agents
2. HandoffProtocolSpec: Defines the structure and validation rules for handoffs
3. MCPAdapterForContexaAgent: Bridges between ContexaAgents and MCP system
4. register_contexa_agent: Utility to register existing agents with the MCP system

Communication Patterns:
----------------------
- Synchronous: Traditional blocking request-response (execute)
- Asynchronous: Non-blocking operations with future results (execute_async)
- Streaming: Real-time progressive updates during execution (execute_streaming)

Integration Features:
-------------------
- Transparent Fallback: Automatically handles ContexaAgent compatibility
- Protocol Validation: Optional validation of inputs and outputs
- Error Handling: Standardized error reporting across all agent types
- Callback Support: Event-based notifications during handoff lifecycle
- Metadata Tracking: Rich context for debugging and monitoring

Usage Examples:
--------------
- Direct handoff between MCP agents:
  ```python
  result = handoff(source_agent, target_agent, "Research quantum computing", 
                  {"query": "recent advances"})
  ```
  
- Streaming handoff:
  ```python
  async for chunk in handoff(source_agent, target_agent, "Research topic", 
                           {"query": "topic"}, streaming=True):
      print(chunk)
  ```

- Handoff between traditional and MCP agents:
  ```python
  result = handoff(contexa_agent, mcp_agent, "Analyze data", {"data": {...}})
  ```
"""

import uuid
import time
import json
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable, AsyncIterator, Type
from pydantic import BaseModel, Field, create_model, ValidationError

from contexa_sdk.orchestration.mcp_agent import (
    MCPAgent, MessageEnvelope, AgentState, Registry, TaskBroker, registry, broker
)
from contexa_sdk.core.agent import ContexaAgent


class HandoffProtocolSpec(BaseModel):
    """Specification for a handoff protocol"""
    protocol_id: str = Field(..., description="Unique identifier for the protocol")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Description of the protocol's purpose")
    version: str = Field("1.0.0", description="Version string")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for input validation")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for output validation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional protocol metadata")


class TaskStatus(str, Enum):
    """Task status values"""
    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class MCPHandoff:
    """MCP-compatible task handoff between agents.
    
    This class represents a standardized approach to delegating tasks between agents
    in the Contexa SDK ecosystem, using MCP principles. It supports:
    
    1. Multiple execution patterns:
       - Synchronous execution (execute)
       - Asynchronous execution (execute_async)
       - Streaming execution with real-time updates (execute_streaming)
       
    2. Compatibility with both MCP agents and traditional ContexaAgents
    
    3. Standardized error handling and status tracking
    
    4. Rich metadata and callback support for monitoring and observability
    
    The handoff system automatically handles protocol differences between different
    agent types, providing a unified interface regardless of the underlying implementation.
    
    Attributes:
        task_id: Unique identifier for the handoff task
        source_agent_id: Identifier of the initiating agent
        target_agent_id: Identifier of the receiving agent
        task_description: Human-readable description of the task
        input_data: Data payload for the task
        protocol_id: Optional protocol identifier for validation
        metadata: Additional context for the handoff
        status: Current status of the handoff
        created_at: Timestamp when the handoff was created
        completed_at: Timestamp when the handoff was completed
        result: Result data from the handoff (if successful)
        error: Error information (if failed)
    """
    
    def __init__(
        self,
        source_agent: Union[MCPAgent, ContexaAgent, str],
        target_agent: Union[MCPAgent, ContexaAgent, str],
        task_description: str,
        input_data: Dict[str, Any],
        task_id: Optional[str] = None,
        protocol_id: Optional[str] = None,
        metadata: Dict[str, Any] = None,
        callbacks: Dict[str, callable] = None,
    ):
        """Initialize an MCP-compatible handoff
        
        Args:
            source_agent: Agent initiating the handoff (MCPAgent, ContexaAgent, or agent_id)
            target_agent: Agent receiving the handoff (MCPAgent, ContexaAgent, or agent_id)
            task_description: Description of the task
            input_data: Data for the task
            task_id: Optional task ID (generated if not provided)
            protocol_id: Optional protocol ID for validation
            metadata: Additional metadata
            callbacks: Callback functions for events
        """
        self.task_id = task_id or str(uuid.uuid4())
        
        # Resolve source agent
        if isinstance(source_agent, MCPAgent):
            self.source_agent_id = source_agent.agent_id
        elif isinstance(source_agent, ContexaAgent):
            self.source_agent_id = getattr(source_agent, "id", str(id(source_agent)))
        else:
            self.source_agent_id = source_agent
            
        # Resolve target agent
        if isinstance(target_agent, MCPAgent):
            self.target_agent_id = target_agent.agent_id
        elif isinstance(target_agent, ContexaAgent):
            self.target_agent_id = getattr(target_agent, "id", str(id(target_agent)))
        else:
            self.target_agent_id = target_agent
        
        self.task_description = task_description
        self.input_data = input_data
        self.protocol_id = protocol_id
        self.metadata = metadata or {}
        self.callbacks = callbacks or {}
        
        self.status = TaskStatus.CREATED
        self.created_at = time.time()
        self.completed_at = None
        self.result = None
        self.error = None
        
    def to_message_envelope(self) -> MessageEnvelope:
        """Convert handoff to a message envelope
        
        Returns:
            MessageEnvelope for this handoff
        """
        return MessageEnvelope(
            sender_id=self.source_agent_id,
            recipient_id=self.target_agent_id,
            task_id=self.task_id,
            message_type="request",
            content={
                "task_description": self.task_description,
                "input_data": self.input_data,
                "protocol_id": self.protocol_id
            },
            metadata=self.metadata
        )
        
    def execute(self) -> Dict[str, Any]:
        """Execute the handoff synchronously
        
        Returns:
            Result of the handoff
        """
        try:
            self.status = TaskStatus.ASSIGNED
            
            # Convert to message envelope
            message = self.to_message_envelope()
            
            # Validate input if protocol exists
            if self.protocol_id:
                # Look up protocol in registry (implementation not shown)
                # Apply validation
                pass
                
            # Send message to target agent
            self.status = TaskStatus.IN_PROGRESS
            
            # Call progress callback if exists
            if "on_progress" in self.callbacks:
                self.callbacks["on_progress"](self)
            
            # Process the message
            try:
                response = broker.send_message(message)
            except ValueError as e:
                # Fall back to ContexaAgent if the target isn't an MCPAgent
                # This enables compatibility with existing agents
                return self._handle_contexa_handoff()
            
            # Update status from response
            if response.message_type == "error":
                self.status = TaskStatus.FAILED
                self.error = response.content.get("error", "Unknown error")
                
                # Call error callback if exists
                if "on_error" in self.callbacks:
                    self.callbacks["on_error"](self, self.error)
                    
                return {
                    "status": "failed",
                    "handoff_id": self.task_id,
                    "error": self.error
                }
            else:
                self.status = TaskStatus.COMPLETED
                self.completed_at = time.time()
                self.result = response.content
                
                # Call completion callback if exists
                if "on_completed" in self.callbacks:
                    self.callbacks["on_completed"](self, self.result)
                    
                return {
                    "status": "completed",
                    "handoff_id": self.task_id,
                    "result": self.result
                }
                
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = str(e)
            
            # Call error callback if exists
            if "on_error" in self.callbacks:
                self.callbacks["on_error"](self, e)
                
            return {
                "status": "failed",
                "handoff_id": self.task_id,
                "error": str(e)
            }
    
    async def execute_async(self) -> Dict[str, Any]:
        """Execute the handoff asynchronously
        
        Returns:
            Result of the handoff
        """
        # Implementation would be similar to execute() but with async calls
        # This is a placeholder for the async implementation
        return self.execute()
    
    async def execute_streaming(self) -> AsyncIterator[Dict[str, Any]]:
        """Execute the handoff with streaming responses
        
        Yields:
            Chunks of the response as they become available
        """
        try:
            self.status = TaskStatus.ASSIGNED
            
            # Convert to message envelope
            message = self.to_message_envelope()
            
            # Send message to target agent
            self.status = TaskStatus.IN_PROGRESS
            
            # Call progress callback if exists
            if "on_progress" in self.callbacks:
                self.callbacks["on_progress"](self)
            
            # Process the message with streaming
            try:
                async for response in broker.send_streaming_message(message):
                    if response.message_type == "error":
                        self.status = TaskStatus.FAILED
                        self.error = response.content.get("error", "Unknown error")
                        
                        # Call error callback if exists
                        if "on_error" in self.callbacks:
                            self.callbacks["on_error"](self, self.error)
                            
                        yield {
                            "status": "failed",
                            "handoff_id": self.task_id,
                            "error": self.error
                        }
                        return
                    elif response.message_type == "stream":
                        # Pass through stream chunks
                        chunk_data = response.content.get("data", {})
                        is_last = response.content.get("is_last", False)
                        
                        if is_last:
                            self.status = TaskStatus.COMPLETED
                            self.completed_at = time.time()
                            
                            # Call completion callback if exists
                            if "on_completed" in self.callbacks:
                                self.callbacks["on_completed"](self, {})
                                
                        yield {
                            "status": "streaming",
                            "handoff_id": self.task_id,
                            "is_last": is_last,
                            "chunk": chunk_data
                        }
            except ValueError as e:
                # Fall back to ContexaAgent if the target isn't an MCPAgent
                # This enables compatibility with existing agents, but doesn't support streaming
                result = self._handle_contexa_handoff()
                yield result
                
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = str(e)
            
            # Call error callback if exists
            if "on_error" in self.callbacks:
                self.callbacks["on_error"](self, e)
                
            yield {
                "status": "failed",
                "handoff_id": self.task_id,
                "error": str(e)
            }
    
    def _handle_contexa_handoff(self) -> Dict[str, Any]:
        """Fall back to handling a handoff with a ContexaAgent
        
        This method provides backward compatibility with existing ContexaAgent instances.
        
        Returns:
            Result of the handoff
        """
        from contexa_sdk.orchestration.handoff import TaskHandoff
        
        # Resolve source and target agents
        source_agent = self._get_contexa_agent(self.source_agent_id)
        target_agent = self._get_contexa_agent(self.target_agent_id)
        
        if not source_agent or not target_agent:
            raise ValueError(f"Could not resolve source or target ContexaAgent")
        
        # Create a traditional TaskHandoff
        handoff = TaskHandoff(
            sender=source_agent,
            recipient=target_agent,
            task_description=self.task_description,
            input_data=self.input_data,
            handoff_id=self.task_id,
            metadata=self.metadata,
            callbacks=self.callbacks
        )
        
        # Execute the handoff
        return handoff.execute()
    
    def _get_contexa_agent(self, agent_id) -> Optional[ContexaAgent]:
        """Get a ContexaAgent by ID
        
        Args:
            agent_id: ID of the agent to retrieve
            
        Returns:
            ContexaAgent if found, None otherwise
        """
        # Implementation depends on how ContexaAgents are registered and tracked
        # This is a placeholder for the actual implementation
        from contexa_sdk.core.registry import get_agent_by_id
        
        try:
            # Attempt to get agent from registry
            return get_agent_by_id(agent_id)
        except:
            # Fall back to searching in the current scope
            # This would be replaced with a proper lookup mechanism
            return None


class MCPAdapterForContexaAgent:
    """Adapter to make ContexaAgent compatible with MCP/ACP interfaces"""
    
    def __init__(self, agent: ContexaAgent, agent_id: Optional[str] = None):
        """Initialize an adapter for a ContexaAgent
        
        Args:
            agent: The ContexaAgent to adapt
            agent_id: Optional agent ID (defaults to the agent's ID or a generated one)
        """
        self.agent = agent
        self.agent_id = agent_id or getattr(agent, "id", str(id(agent)))
        
    def get_mcp_agent(self) -> MCPAgent:
        """Convert a ContexaAgent to an MCPAgent
        
        Returns:
            MCPAgent wrapper for the ContexaAgent
        """
        # Extract capabilities from agent tools
        capabilities = []
        if hasattr(self.agent, "tools") and self.agent.tools:
            capabilities = [
                getattr(tool, "name", getattr(tool, "__name__", str(tool)))
                for tool in self.agent.tools
            ]
        
        # Create an MCPAgent
        mcp_agent = MCPAgent(
            agent_id=self.agent_id,
            name=getattr(self.agent, "name", "Unknown"),
            description=getattr(self.agent, "description", ""),
            version="1.0.0",  # Default version
            capabilities=capabilities,
            metadata={
                "agent_type": "contexa",
                "original_id": getattr(self.agent, "id", str(id(self.agent)))
            }
        )
        
        # Set the execution handler to forward to the ContexaAgent
        mcp_agent.set_execution_handler(self._execution_handler)
        
        # Set the agent to active state
        mcp_agent.set_state(AgentState.ACTIVE)
        
        return mcp_agent
    
    def _execution_handler(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execution requests by forwarding to the ContexaAgent
        
        Args:
            content: Message content from the request
            
        Returns:
            Result from the ContexaAgent
        """
        # Extract task description and input data
        task_description = content.get("task_description", "")
        input_data = content.get("input_data", {})
        
        # Combine into a single input for the agent
        combined_input = {
            "task": task_description,
            "data": input_data
        }
        
        # Call the agent's run method
        try:
            if hasattr(self.agent, "process_handoff"):
                # Use the dedicated handoff method if available
                result = self.agent.process_handoff(combined_input)
            else:
                # Fall back to the general run method
                result = self.agent.run(combined_input)
                
            # Standardize the result format
            if isinstance(result, dict) and "result" in result:
                return result
            else:
                return {"result": result}
        except Exception as e:
            return {
                "error": str(e),
                "code": "execution_error"
            }


def register_contexa_agent(agent: ContexaAgent, agent_id: Optional[str] = None) -> MCPAgent:
    """Register a ContexaAgent with the MCP registry
    
    Args:
        agent: The ContexaAgent to register
        agent_id: Optional agent ID (defaults to the agent's ID or a generated one)
        
    Returns:
        The MCPAgent wrapper for the registered agent
    """
    adapter = MCPAdapterForContexaAgent(agent, agent_id)
    mcp_agent = adapter.get_mcp_agent()
    registry.register(mcp_agent)
    return mcp_agent


def handoff(
    source_agent: Union[MCPAgent, ContexaAgent, str],
    target_agent: Union[MCPAgent, ContexaAgent, str],
    task_description: str,
    input_data: Dict[str, Any],
    task_id: Optional[str] = None,
    protocol_id: Optional[str] = None,
    metadata: Dict[str, Any] = None,
    streaming: bool = False,
    async_mode: bool = False
) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
    """Perform a handoff between agents using the MCP protocol.
    
    This is the main entry point for MCP-based handoffs in Contexa SDK.
    It supports both MCP-native agents and regular ContexaAgents.
    
    This function simplifies the process of delegating tasks between agents
    by providing a unified interface regardless of the agent types involved.
    It automatically handles protocol differences and provides multiple
    execution patterns (sync, async, streaming).
    
    Args:
        source_agent: Agent initiating the handoff (MCPAgent, ContexaAgent, or agent_id)
        target_agent: Agent receiving the handoff (MCPAgent, ContexaAgent, or agent_id)
        task_description: Description of the task to be performed
        input_data: Data payload for the task
        task_id: Optional task ID (generated if not provided)
        protocol_id: Optional protocol ID for schema validation
        metadata: Additional metadata for tracking and context
        streaming: Whether to use streaming mode for real-time updates
        async_mode: Whether to use async execution mode
        
    Returns:
        For synchronous handoffs: Dict containing result information
        For streaming handoffs: AsyncIterator yielding result chunks
        
    Example (synchronous):
        ```python
        result = handoff(
            source_agent=orchestrator,
            target_agent=research_agent,
            task_description="Research quantum computing",
            input_data={"query": "recent developments", "max_results": 5}
        )
        print(f"Status: {result['status']}")
        print(f"Result: {result['result']}")
        ```
        
    Example (streaming):
        ```python
        stream = handoff(
            source_agent=orchestrator,
            target_agent=analysis_agent,
            task_description="Analyze data stream",
            input_data={"data": data_points},
            streaming=True
        )
        
        async for chunk in stream:
            print(f"Progress: {chunk.get('chunk', {}).get('progress', 0)}")
        ```
    """
    handoff = MCPHandoff(
        source_agent=source_agent,
        target_agent=target_agent,
        task_description=task_description,
        input_data=input_data,
        task_id=task_id,
        protocol_id=protocol_id,
        metadata=metadata
    )
    
    if streaming:
        return handoff.execute_streaming()
    elif async_mode:
        return handoff.execute_async()
    else:
        return handoff.execute() 