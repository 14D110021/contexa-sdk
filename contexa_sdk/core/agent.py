"""Agent module for Contexa SDK.

This module provides framework-agnostic agent implementations for the Contexa SDK.
It defines the core agent classes, memory management, and agent-to-agent handoff
capabilities that form the foundation of the agent runtime system.

The module supports both local agents (ContexaAgent) and remote agents (RemoteAgent),
enabling seamless interaction regardless of where agents are deployed.

Examples:
    Create and run a local agent:
    
    ```python
    from contexa_sdk.core.agent import ContexaAgent
    from contexa_sdk.core.model import ContexaModel
    from contexa_sdk.core.tool import ContexaTool
    
    # Create an agent with a model and tools
    agent = ContexaAgent(
        name="My Assistant",
        description="A helpful assistant",
        model=ContexaModel(provider="openai", model_id="gpt-4o"),
        tools=[web_search_tool],
        system_prompt="You are a helpful assistant specialized in research."
    )
    
    # Run the agent
    response = await agent.run("What's the latest news on AI?")
    print(response)
    ```
    
    Perform an agent handoff:
    
    ```python
    # Hand off from one agent to another
    result = await research_agent.handoff_to(
        writing_agent,
        query="Write a summary of the research findings",
        include_history=True
    )
    ```
"""

import uuid
import json
import httpx
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar

from pydantic import BaseModel, Field

from contexa_sdk.core.config import ContexaConfig
from contexa_sdk.core.model import ContexaModel, ModelMessage
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.prompt import ContexaPrompt

# Import observability modules
from contexa_sdk.observability.logger import get_logger
from contexa_sdk.observability.tracer import trace, SpanKind, Span
from contexa_sdk.observability.metrics import Timer, agent_requests, agent_latency, model_tokens, tool_calls, tool_latency, handoffs, active_agents

# Create a logger for this module
logger = get_logger(__name__)

# Type variable for agent types
AgentT = TypeVar('AgentT')


class HandoffData(BaseModel):
    """Data structure for agent handoffs.
    
    This model represents the data exchanged during an agent-to-agent handoff.
    It contains the query, context, and metadata needed for the target agent
    to continue processing where the source agent left off.
    
    Attributes:
        query (str): The query to send to the target agent
        result (Optional[str]): The result from the target agent (if available)
        context (Dict[str, Any]): Additional context data for the target agent
        metadata (Dict[str, Any]): Additional metadata about the handoff
        source_agent_id (Optional[str]): ID of the source agent
        source_agent_name (Optional[str]): Name of the source agent
    """
    
    query: str
    result: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_agent_id: Optional[str] = None
    source_agent_name: Optional[str] = None
    

class AgentMemory(BaseModel):
    """Memory for an agent.
    
    Stores the conversation history, metadata, and handoff history for an agent.
    The memory provides methods to add and retrieve messages, manage handoffs,
    and serialize/deserialize the memory state.
    
    Attributes:
        messages (List[ModelMessage]): The conversation history
        metadata (Dict[str, Any]): Additional metadata for the agent
        handoff_history (List[HandoffData]): History of handoffs involving this agent
    """
    
    messages: List[ModelMessage] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    handoff_history: List[HandoffData] = Field(default_factory=list)
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the memory.
        
        Args:
            role (str): The role of the message sender ("system", "user", "assistant")
            content (str): The content of the message
        """
        self.messages.append(ModelMessage(role=role, content=content))
        
    def get_messages(self) -> List[ModelMessage]:
        """Get all messages in the memory.
        
        Returns:
            List[ModelMessage]: The list of all messages in memory
        """
        return self.messages
        
    def clear(self) -> None:
        """Clear the memory.
        
        Removes all messages from memory, but preserves metadata and handoff history.
        """
        self.messages = []
        
    def add_handoff(self, handoff_data: HandoffData) -> None:
        """Add a handoff to the memory.
        
        Args:
            handoff_data (HandoffData): The handoff data to add to memory
        """
        self.handoff_history.append(handoff_data)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the memory
        """
        return {
            "messages": [m.model_dump() for m in self.messages],
            "metadata": self.metadata,
            "handoff_history": [h.model_dump() for h in self.handoff_history],
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMemory":
        """Create an AgentMemory from a dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary representation of the memory
            
        Returns:
            AgentMemory: Reconstructed memory object
        """
        return cls(
            messages=[ModelMessage(**m) for m in data.get("messages", [])],
            metadata=data.get("metadata", {}),
            handoff_history=[HandoffData(**h) for h in data.get("handoff_history", [])],
        )


class ContexaAgent:
    """Framework-agnostic wrapper for agents.
    
    ContexaAgent provides a unified interface for creating and running AI agents
    with different language models and tools. It handles conversation management,
    tool execution, and agent handoffs, with built-in observability through
    logging, tracing, and metrics.
    
    The agent implements a basic reasoning loop that:
    1. Processes user input
    2. Generates a response using the language model
    3. Detects and executes tool calls when needed
    4. Generates a final response incorporating tool results
    
    This base implementation can be extended or adapted to different agent
    frameworks through the adapter pattern.
    
    Attributes:
        tools (List[ContexaTool]): List of tools available to the agent
        model (ContexaModel): Language model used by the agent
        system_prompt (str): System prompt providing instructions to the model
        name (str): Name of the agent
        description (str): Description of the agent's capabilities
        version (str): Version string for the agent
        config (ContexaConfig): Configuration for the agent
        agent_id (str): Unique identifier for the agent
        memory (AgentMemory): Memory storing conversation and handoff history
    """
    
    def __init__(
        self,
        tools: List[ContexaTool],
        model: ContexaModel,
        system_prompt: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        version: str = "0.1.0",
        config: Optional[ContexaConfig] = None,
        agent_id: Optional[str] = None,
        memory: Optional[AgentMemory] = None,
    ):
        """Initialize a ContexaAgent.
        
        Args:
            tools: List of tools available to the agent
            model: Language model to use for the agent
            system_prompt: System prompt for the agent
            name: Name of the agent
            description: Description of the agent
            version: Version of the agent
            config: Configuration for the agent
            agent_id: Unique ID for the agent (auto-generated if not provided)
            memory: Memory for the agent
        """
        self.tools = tools
        self.model = model
        self.system_prompt = system_prompt or (
            "You are a helpful AI assistant. "
            "You have access to tools that you can use to help answer questions."
        )
        self.name = name or "unnamed_agent"
        self.description = description or ""
        self.version = version
        self.config = config or ContexaConfig()
        self.agent_id = agent_id or str(uuid.uuid4())
        self.memory = memory or AgentMemory()
        
        # Increment active agents count
        active_agents.inc()
        
        # Log agent creation
        logger.info(f"Agent created: {self.name} ({self.agent_id})")
        
    def __del__(self):
        """Destructor to handle cleanup when agent is garbage collected."""
        # Decrement active agents count
        active_agents.dec()
    
    @trace(kind=SpanKind.AGENT)
    async def run(self, query: str) -> str:
        """Run the agent on a query.
        
        This method implements the core agent execution loop:
        1. Add the user query to memory
        2. Generate a response using the model
        3. Parse and execute any tool calls
        4. Generate a final response incorporating tool results
        
        This implementation can be overridden by framework-specific adapters.
        
        Args:
            query (str): The query to run the agent on
            
        Returns:
            str: The agent's response
            
        Raises:
            Exception: Any errors encountered during agent execution
        """
        # Start metrics timer
        with Timer(agent_latency, agent_id=self.agent_id, agent_name=self.name):
            # Add user message to memory
            self.memory.add_message("user", query)
            
            # Log the query
            logger.info(
                f"Running agent {self.name} ({self.agent_id})",
                extra={
                    "agent_id": self.agent_id,
                    "query": query,
                    "memory_size": len(self.memory.messages)
                }
            )
            
            # Format messages for the model
            messages = [
                ModelMessage(role="system", content=self.system_prompt),
                *self.memory.get_messages(),
            ]
            
            # Tool descriptions for the model
            tool_descriptions = []
            for tool in self.tools:
                tool_descriptions.append(
                    f"- {tool.name}: {tool.description}\n"
                    f"  Parameters: {tool.schema.model_json_schema()}\n"
                )
                
            if tool_descriptions:
                tool_message = (
                    "You have access to the following tools:\n\n" +
                    "\n".join(tool_descriptions) +
                    "\n\nTo use a tool, respond in the format:\n" +
                    "```tool\n{\"name\": \"tool_name\", \"parameters\": {\"param1\": \"value1\"}}\n```"
                )
                messages.append(ModelMessage(role="system", content=tool_message))
                
            try:
                # Create span for model generation
                with Span(name=f"model.generate", kind=SpanKind.MODEL) as span:
                    span.set_attribute("model.name", self.model.model_name)
                    span.set_attribute("model.provider", self.model.provider)
                    span.set_attribute("input.tokens", self._estimate_tokens(messages))
                    
                    # Generate a response
                    response = await self.model.generate(messages)
                    
                    # Record output token metrics
                    output_tokens = self._estimate_tokens([response])
                    model_tokens.inc(output_tokens, model_name=self.model.model_name, provider=self.model.provider, type="output")
                    span.set_attribute("output.tokens", output_tokens)
                
                # Parse potential tool calls
                output = response.content
                
                if "```tool" in output and "```" in output.split("```tool", 1)[1]:
                    # Extract tool call
                    tool_text = output.split("```tool", 1)[1].split("```", 1)[0].strip()
                    
                    import json
                    try:
                        tool_call = json.loads(tool_text)
                        tool_name = tool_call["name"]
                        tool_params = tool_call["parameters"]
                        
                        # Find the tool
                        tool = next((t for t in self.tools if t.name == tool_name), None)
                        if tool:
                            # Create span and increment metrics for tool call
                            with Span(name=f"tool.{tool_name}", kind=SpanKind.TOOL) as span:
                                span.set_attribute("tool.name", tool_name)
                                span.set_attribute("tool.parameters", json.dumps(tool_params))
                                
                                # Add the tool call to memory
                                self.memory.add_message(
                                    "assistant", 
                                    f"I'll use the {tool_name} tool with parameters: {json.dumps(tool_params)}"
                                )
                                
                                # Record tool call metric
                                tool_calls.inc(1, tool_name=tool_name, agent_id=self.agent_id, status="success")
                                
                                # Measure tool execution time
                                with Timer(tool_latency, tool_name=tool_name, agent_id=self.agent_id):
                                    # Call the tool
                                    tool_result = await tool(**tool_params)
                                
                                # Add the tool result to memory
                                self.memory.add_message(
                                    "system", 
                                    f"Tool result: {tool_result}"
                                )
                                
                                span.set_attribute("tool.result", str(tool_result))
                            
                            # Generate a final response
                            with Span(name=f"model.final_response", kind=SpanKind.MODEL) as span:
                                final_messages = [
                                    ModelMessage(role="system", content=self.system_prompt),
                                    *self.memory.get_messages(),
                                    ModelMessage(
                                        role="system", 
                                        content=(
                                            "Please provide a final response to the user based on "
                                            "the tool result. Don't mention the tool explicitly."
                                        )
                                    ),
                                ]
                                
                                # Record input token metrics
                                input_tokens = self._estimate_tokens(final_messages)
                                model_tokens.inc(input_tokens, model_name=self.model.model_name, provider=self.model.provider, type="input")
                                span.set_attribute("input.tokens", input_tokens)
                                
                                # Generate final response
                                final_response = await self.model.generate(final_messages)
                                
                                # Record output token metrics
                                output_tokens = self._estimate_tokens([final_response])
                                model_tokens.inc(output_tokens, model_name=self.model.model_name, provider=self.model.provider, type="output")
                                span.set_attribute("output.tokens", output_tokens)
                                
                                output = final_response.content
                    except (json.JSONDecodeError, KeyError) as e:
                        # If tool call parsing fails, just return the original response
                        logger.warning(
                            f"Failed to parse tool call: {e}",
                            extra={
                                "agent_id": self.agent_id,
                                "tool_text": tool_text,
                            }
                        )
                        # Record failed tool call metric
                        tool_calls.inc(1, tool_name="unknown", agent_id=self.agent_id, status="error")
                        
                # Add assistant message to memory
                self.memory.add_message("assistant", output)
                
                # Increment successful request count
                agent_requests.inc(1, agent_id=self.agent_id, agent_name=self.name, status="success")
                
                return output
            except Exception as e:
                # Log the error
                logger.error(
                    f"Error running agent {self.name} ({self.agent_id}): {str(e)}",
                    extra={
                        "agent_id": self.agent_id,
                        "error": str(e),
                    }
                )
                
                # Increment failed request count
                agent_requests.inc(1, agent_id=self.agent_id, agent_name=self.name, status="error")
                
                # Re-raise the exception
                raise
    
    @trace(kind=SpanKind.HANDOFF)
    async def handoff_to(
        self, 
        target_agent: AgentT, 
        query: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        include_history: bool = False,
    ) -> str:
        """Hand off processing to another agent with context.
        
        This method enables agent-to-agent collaboration by transferring control
        from this agent to another agent, optionally including conversation history
        and context. It preserves the continuity of the conversation and provides
        a way for agents to delegate tasks to more specialized agents.
        
        Args:
            target_agent (AgentT): The agent to hand off to
            query (Optional[str]): Optional new query to send to the target agent
                  (default: last query this agent received)
            context (Optional[Dict[str, Any]]): Additional context data to pass to the target agent
            metadata (Optional[Dict[str, Any]]): Additional metadata for the handoff
            include_history (bool): Whether to include message history in the handoff
            
        Returns:
            str: The target agent's response
            
        Raises:
            ValueError: If no query is provided and no previous user query found
            NotImplementedError: If handoff to a framework-specific agent is attempted
            Exception: Any errors encountered during the handoff
        """
        # Start a span for the handoff
        with Span(name=f"handoff.{self.name}_to_{getattr(target_agent, 'name', 'unknown')}", kind=SpanKind.HANDOFF) as span:
            # Get target agent metadata for logging and metrics
            target_agent_id = getattr(target_agent, "agent_id", "unknown")
            target_agent_name = getattr(target_agent, "name", "unknown")
            
            span.set_attribute("handoff.source_agent_id", self.agent_id)
            span.set_attribute("handoff.source_agent_name", self.name)
            span.set_attribute("handoff.target_agent_id", target_agent_id)
            span.set_attribute("handoff.target_agent_name", target_agent_name)
            
            # Determine the query to use
            if query is None and self.memory.messages:
                # Find the last user query from memory
                for msg in reversed(self.memory.messages):
                    if msg.role == "user":
                        query = msg.content
                        break
            
            if query is None:
                error_msg = "No query provided and no previous user query found in memory"
                logger.error(
                    f"Handoff failed: {error_msg}",
                    extra={
                        "source_agent_id": self.agent_id,
                        "target_agent_id": target_agent_id,
                    }
                )
                raise ValueError(error_msg)
                
            # Log the handoff
            logger.info(
                f"Handoff from {self.name} ({self.agent_id}) to {target_agent_name} ({target_agent_id})",
                extra={
                    "source_agent_id": self.agent_id,
                    "target_agent_id": target_agent_id,
                    "query": query,
                }
            )
            
            # Create handoff data
            handoff_data = HandoffData(
                query=query,
                context=context or {},
                metadata=metadata or {},
                source_agent_id=self.agent_id,
                source_agent_name=self.name,
            )
            
            # Add context from this agent's memory if requested
            if include_history:
                handoff_data.context["source_agent_memory"] = self.memory.to_dict()
            
            # Record the handoff in this agent's memory
            self.memory.add_handoff(handoff_data)
            
            # Record handoff metric
            handoffs.inc(1, source_agent_id=self.agent_id, target_agent_id=target_agent_id, status="initiated")
            
            try:
                # Determine if the target agent is a ContexaAgent or a framework-specific agent
                if isinstance(target_agent, ContexaAgent):
                    # For ContexaAgent targets, we can directly handle the handoff
                    # Add a system message about the handoff
                    handoff_msg = (
                        f"This is a task handoff from agent '{self.name}' (ID: {self.agent_id}). "
                        f"Previous context: {json.dumps(handoff_data.context)}"
                    )
                    
                    target_agent.memory.add_message("system", handoff_msg)
                    
                    # Run the target agent with the query
                    result = await target_agent.run(query)
                    
                    # Update the handoff data with the result
                    handoff_data.result = result
                    
                    # Record successful handoff metric
                    handoffs.inc(1, source_agent_id=self.agent_id, target_agent_id=target_agent_id, status="success")
                    
                    span.set_attribute("handoff.result", result)
                    
                    return result
                else:
                    # For framework-specific agents, we need to let the framework adapter handle it
                    # The actual implementation will be in the adapter
                    error_msg = "Handoff to framework-specific agents must be handled by the framework adapter"
                    logger.error(
                        f"Handoff failed: {error_msg}",
                        extra={
                            "source_agent_id": self.agent_id,
                            "target_agent_id": target_agent_id,
                        }
                    )
                    
                    # Record failed handoff metric
                    handoffs.inc(1, source_agent_id=self.agent_id, target_agent_id=target_agent_id, status="error")
                    
                    raise NotImplementedError(error_msg)
            except Exception as e:
                # Record failed handoff metric
                handoffs.inc(1, source_agent_id=self.agent_id, target_agent_id=target_agent_id, status="error")
                
                # Log the error
                logger.error(
                    f"Error during handoff: {str(e)}",
                    extra={
                        "source_agent_id": self.agent_id,
                        "target_agent_id": target_agent_id,
                        "error": str(e),
                    }
                )
                
                raise
    
    def prepare_handoff_data(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> HandoffData:
        """Prepare handoff data for another agent.
        
        This method creates a HandoffData object that can be used for a handoff
        without actually performing the handoff. This is useful for cross-framework
        handoffs where the framework adapter needs to handle the handoff process.
        
        Args:
            query (str): The query to send to the target agent
            context (Optional[Dict[str, Any]]): Additional context data for the target agent
            metadata (Optional[Dict[str, Any]]): Additional metadata for the handoff
            
        Returns:
            HandoffData: Object ready for a handoff
        """
        return HandoffData(
            query=query,
            context=context or {},
            metadata=metadata or {},
            source_agent_id=self.agent_id,
            source_agent_name=self.name,
        )
    
    def receive_handoff(self, handoff_data: HandoffData) -> None:
        """Receive a handoff from another agent.
        
        This method prepares this agent to handle a task that was handed off
        from another agent by adding the context to this agent's memory.
        
        Args:
            handoff_data (HandoffData): The handoff data from the source agent
        """
        # Add the handoff data to this agent's memory
        self.memory.add_handoff(handoff_data)
        
        # Add a system message about the handoff
        handoff_msg = (
            f"This is a task handoff from agent '{handoff_data.source_agent_name}' "
            f"(ID: {handoff_data.source_agent_id}). "
            f"Previous context: {json.dumps(handoff_data.context)}"
        )
        
        self.memory.add_message("system", handoff_msg)
        
        # Log the received handoff
        logger.info(
            f"Received handoff to {self.name} ({self.agent_id}) from {handoff_data.source_agent_name} ({handoff_data.source_agent_id})",
            extra={
                "source_agent_id": handoff_data.source_agent_id,
                "target_agent_id": self.agent_id,
                "query": handoff_data.query,
            }
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the agent to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "version": self.version,
            "agent_id": self.agent_id,
            "tools": [tool.to_dict() for tool in self.tools],
            "model": {
                "model_name": self.model.model_name,
                "provider": self.model.provider,
            },
            "memory": self.memory.to_dict() if self.memory else None,
        }
        
    @classmethod
    def from_dict(
        cls, 
        data: Dict[str, Any],
        tools: Optional[List[ContexaTool]] = None,
        model: Optional[ContexaModel] = None,
        config: Optional[ContexaConfig] = None,
    ) -> "ContexaAgent":
        """Create an agent from a dictionary.
        
        Args:
            data: Dictionary representation of the agent
            tools: List of tools to use (overrides tools in data)
            model: Model to use (overrides model in data)
            config: Configuration to use
            
        Returns:
            A ContexaAgent
        """
        # Use provided tools or load from data
        if tools is None:
            # Handle tool loading in a real implementation
            tools = []
            
        # Use provided model or load from data
        if model is None:
            model_data = data.get("model", {})
            model = ContexaModel(
                model_name=model_data.get("model_name", "gpt-3.5-turbo"),
                provider=model_data.get("provider", "openai"),
                config=config,
            )
        
        # Load memory if provided
        memory = None
        if "memory" in data and data["memory"]:
            memory = AgentMemory.from_dict(data["memory"])
            
        return cls(
            tools=tools,
            model=model,
            system_prompt=data.get("system_prompt"),
            name=data.get("name"),
            description=data.get("description"),
            version=data.get("version", "0.1.0"),
            config=config,
            agent_id=data.get("agent_id"),
            memory=memory,
        )
    
    def _estimate_tokens(self, messages: List[ModelMessage]) -> int:
        """Estimate the number of tokens in a list of messages.
        
        Args:
            messages: List of messages
            
        Returns:
            Estimated token count
        """
        # This is a simple estimation - about 4 chars per token
        total_chars = 0
        for message in messages:
            total_chars += len(message.role) + len(message.content or "")
        
        return total_chars // 4


class RemoteAgent:
    """Agent that calls a remote MCP-compatible agent server.
    
    This class allows interacting with an agent hosted as an MCP server,
    making it appear as a local agent while actually executing remotely.
    """
    
    def __init__(
        self,
        endpoint_url: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[ContexaConfig] = None,
        agent_id: Optional[str] = None,
        memory: Optional[AgentMemory] = None,
    ):
        """Initialize a RemoteAgent.
        
        Args:
            endpoint_url: URL of the MCP-compatible agent server
            name: Name of the agent (if not provided, will be fetched from the server)
            description: Description of the agent
            config: Configuration for API requests
            agent_id: Unique ID for the agent (auto-generated if not provided)
            memory: Memory for the agent
        """
        self.endpoint_url = endpoint_url
        self.config = config or ContexaConfig()
        self.agent_id = agent_id or str(uuid.uuid4())
        self.memory = memory or AgentMemory()
        self._name = name
        self._description = description
        self._initialized = False
        
    async def _initialize(self) -> None:
        """Initialize the agent by fetching metadata from the remote server."""
        if self._initialized:
            return
            
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                # Fetch agent information from the MCP server
                headers = {"Content-Type": "application/json"}
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"
                    
                response = await client.get(
                    f"{self.endpoint_url}/api/v1/agent/info",
                    headers=headers,
                )
                response.raise_for_status()
                agent_info = response.json()
                
                # Set agent properties from the response
                if not self._name:
                    self._name = agent_info.get("name", "remote_agent")
                if not self._description:
                    self._description = agent_info.get("description", "")
                
                self._initialized = True
        except Exception as e:
            # If initialization fails, use default values
            if not self._name:
                self._name = "remote_agent"
            if not self._description:
                self._description = f"Remote agent at {self.endpoint_url}"
            self._initialized = True
    
    @property
    async def name(self) -> str:
        """Get the agent name (may require API call if not set)."""
        await self._initialize()
        return self._name
        
    @property
    async def description(self) -> str:
        """Get the agent description (may require API call if not set)."""
        await self._initialize()
        return self._description
    
    async def run(self, query: str) -> str:
        """Run the agent on a query.
        
        Args:
            query: The query to run the agent on
            
        Returns:
            The agent's response
        """
        # Ensure the agent is initialized
        await self._initialize()
        
        # Add user message to memory
        self.memory.add_message("user", query)
        
        # Prepare the request payload
        payload = {
            "query": query,
            "memory": self.memory.to_dict(),
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                # Call the MCP agent server
                headers = {"Content-Type": "application/json"}
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"
                    
                response = await client.post(
                    f"{self.endpoint_url}/api/v1/agent/run",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract the result and update memory
                output = result.get("result", "No response from remote agent")
                
                # If the server returned updated memory, use it
                if "memory" in result:
                    self.memory = AgentMemory.from_dict(result["memory"])
                else:
                    # Otherwise, just add the response to our local memory
                    self.memory.add_message("assistant", output)
                
                return output
        except Exception as e:
            error_msg = f"Error calling remote agent: {str(e)}"
            self.memory.add_message("system", error_msg)
            return error_msg
    
    async def handoff_to(
        self, 
        target_agent: Any, 
        query: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Hand off processing to another agent.
        
        This method forwards the handoff request to the remote agent server.
        
        Args:
            target_agent: The agent to hand off to
            query: Optional new query to send to the target agent
            context: Additional context data to pass to the target agent
            metadata: Additional metadata for the handoff
            
        Returns:
            The target agent's response
        """
        # Determine the query to use
        if query is None and self.memory.messages:
            # Find the last user query from memory
            for msg in reversed(self.memory.messages):
                if msg.role == "user":
                    query = msg.content
                    break
        
        if query is None:
            raise ValueError("No query provided and no previous user query found in memory")
        
        # For remote agents, we may not be able to directly hand off to another agent
        # since the remote agent is actually running on the server
        # Instead, we'll call our own run method with a special query format
        handoff_query = (
            f"[HANDOFF]\n"
            f"TARGET: {getattr(target_agent, 'name', 'unknown')}\n"
            f"QUERY: {query}\n"
            f"CONTEXT: {json.dumps(context or {})}\n"
        )
        
        return await self.run(handoff_query)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the agent to a dictionary."""
        return {
            "agent_type": "remote",
            "endpoint_url": self.endpoint_url,
            "name": self._name,
            "description": self._description,
            "agent_id": self.agent_id,
            "memory": self.memory.to_dict() if self.memory else None,
        }
        
    @classmethod
    async def from_endpoint(
        cls,
        endpoint_url: str,
        config: Optional[ContexaConfig] = None,
    ) -> "RemoteAgent":
        """Create a RemoteAgent from an endpoint URL.
        
        This method will fetch the agent metadata from the endpoint
        and create a properly configured RemoteAgent.
        
        Args:
            endpoint_url: URL of the MCP-compatible agent server
            config: Configuration for API requests
            
        Returns:
            A configured RemoteAgent
        """
        agent = cls(
            endpoint_url=endpoint_url,
            config=config,
        )
        
        # Initialize the agent, which will fetch metadata
        await agent._initialize()
        
        return agent 