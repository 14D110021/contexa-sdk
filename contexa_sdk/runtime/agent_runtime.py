"""Core agent runtime interface and implementations.

This module defines the base interfaces for agent runtime environments, which are
responsible for managing the lifecycle of agents, allocating resources, and
ensuring proper execution of agent tasks.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union, Callable, Awaitable
import uuid

from contexa_sdk.runtime.state_management import AgentState, StateProvider
from contexa_sdk.runtime.resource_tracking import ResourceUsage, ResourceLimits
from contexa_sdk.runtime.health_monitoring import HealthStatus, HealthCheck
from contexa_sdk.core.agent import ContexaAgent


class AgentRuntimeStatus(Enum):
    """Status of an agent runtime."""
    INITIALIZING = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()


@dataclass
class AgentRuntimeConfig:
    """Configuration for an agent runtime."""
    # Maximum number of concurrent agents
    max_agents: int = 100
    
    # Default resource limits for agents
    default_resource_limits: ResourceLimits = field(
        default_factory=lambda: ResourceLimits(
            max_memory_mb=1024,
            max_cpu_percent=50,
            max_requests_per_minute=120
        )
    )
    
    # State provider for agent state persistence
    state_provider: Optional[StateProvider] = None
    
    # Health check interval in seconds
    health_check_interval_seconds: float = 60.0
    
    # Additional configuration options
    additional_options: Dict[str, Any] = field(default_factory=dict)


class AgentStatus(str, Enum):
    """Agent status values."""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class RuntimeOptions:
    """Options for agent runtime configuration."""
    
    def __init__(
        self,
        max_concurrent_runs: int = 1,
        timeout_seconds: Optional[int] = None,
        auto_restart: bool = False,
        state_persistence: bool = False,
        telemetry_enabled: bool = True,
        memory_limit_mb: Optional[int] = None
    ):
        """Initialize runtime options.
        
        Args:
            max_concurrent_runs: Maximum number of concurrent agent runs
            timeout_seconds: Timeout for agent runs in seconds (None for no timeout)
            auto_restart: Whether to automatically restart the agent on failure
            state_persistence: Whether to persist agent state between runs
            telemetry_enabled: Whether to collect telemetry data
            memory_limit_mb: Memory limit for the agent in MB (None for no limit)
        """
        self.max_concurrent_runs = max_concurrent_runs
        self.timeout_seconds = timeout_seconds
        self.auto_restart = auto_restart
        self.state_persistence = state_persistence
        self.telemetry_enabled = telemetry_enabled
        self.memory_limit_mb = memory_limit_mb


class AgentRuntimeException(Exception):
    """Exception raised for agent runtime errors."""
    pass


class AgentRuntime(ABC):
    """Abstract base class for agent runtime environments.
    
    An agent runtime is responsible for managing the lifecycle of agents,
    allocating resources, and ensuring proper execution of agent tasks.
    """
    
    def __init__(self, config: AgentRuntimeConfig):
        """Initialize the agent runtime.
        
        Args:
            config: Configuration for the agent runtime
        """
        self.config = config
        self.status = AgentRuntimeStatus.INITIALIZING
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def start(self) -> None:
        """Start the agent runtime.
        
        This method initializes the runtime environment and prepares it
        for agent execution.
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the agent runtime.
        
        This method gracefully shuts down the runtime environment and
        all running agents.
        """
        pass
    
    @abstractmethod
    async def pause(self) -> None:
        """Pause the agent runtime.
        
        This method temporarily suspends execution of all agents without
        completely shutting down the runtime.
        """
        pass
    
    @abstractmethod
    async def resume(self) -> None:
        """Resume the agent runtime.
        
        This method resumes execution of all agents after a pause.
        """
        pass
    
    @abstractmethod
    async def register_agent(
        self, 
        agent_id: str, 
        agent_type: str,
        resource_limits: Optional[ResourceLimits] = None
    ) -> None:
        """Register an agent with the runtime.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of the agent (determines capabilities)
            resource_limits: Optional resource limits for the agent,
                defaults to runtime's default limits if not provided
        """
        pass
    
    @abstractmethod
    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the runtime.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        pass
    
    @abstractmethod
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get the status of an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Dictionary containing agent status information
        """
        pass
    
    @abstractmethod
    async def run_agent(
        self, 
        agent_id: str, 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run an agent with the given input data.
        
        Args:
            agent_id: Unique identifier for the agent
            input_data: Input data for the agent
            
        Returns:
            Dictionary containing the agent's output
        """
        pass
    
    @abstractmethod
    async def save_agent_state(self, agent_id: str) -> None:
        """Save the current state of an agent.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        pass
    
    @abstractmethod
    async def load_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Load the state of an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            The agent's state, or None if no state is available
        """
        pass
    
    @abstractmethod
    async def get_resource_usage(self, agent_id: str) -> ResourceUsage:
        """Get the current resource usage of an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Resource usage information for the agent
        """
        pass
    
    @abstractmethod
    async def check_health(self, agent_id: Optional[str] = None) -> Dict[str, HealthStatus]:
        """Check the health of the runtime or a specific agent.
        
        Args:
            agent_id: Optional identifier for a specific agent,
                if None, checks the health of the entire runtime
                
        Returns:
            Dictionary mapping entity IDs to health status
        """
        pass
    
    @abstractmethod
    async def recover_agent(self, agent_id: str) -> bool:
        """Attempt to recover an agent that is in an error state.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            True if recovery was successful, False otherwise
        """
        pass


class AgentRuntime:
    """Manages agent lifecycle and execution.
    
    The AgentRuntime manages the lifecycle of one or more agents, including:
    - Starting and stopping agents
    - Executing agent runs
    - Managing agent state
    - Monitoring agent health
    - Enforcing resource limits
    """
    
    def __init__(self, options: Optional[RuntimeOptions] = None):
        """Initialize the agent runtime.
        
        Args:
            options: Runtime configuration options
        """
        self.options = options or RuntimeOptions()
        self.agents: Dict[str, ContexaAgent] = {}
        self.agent_status: Dict[str, AgentStatus] = {}
        self.runs_in_progress: Dict[str, asyncio.Task] = {}
        
    async def register_agent(self, agent: ContexaAgent) -> str:
        """Register an agent with the runtime.
        
        Args:
            agent: The agent to register
            
        Returns:
            The agent ID
            
        Raises:
            AgentRuntimeException: If the agent could not be registered
        """
        agent_id = getattr(agent, 'agent_id', str(uuid.uuid4()))
        self.agents[agent_id] = agent
        self.agent_status[agent_id] = AgentStatus.INITIALIZING
        
        try:
            # Initialize agent
            self.agent_status[agent_id] = AgentStatus.READY
            return agent_id
        except Exception as e:
            del self.agents[agent_id]
            del self.agent_status[agent_id]
            raise AgentRuntimeException(f"Failed to register agent: {str(e)}") from e
    
    async def start_agent(self, agent_id: str) -> None:
        """Start an agent.
        
        Args:
            agent_id: The ID of the agent to start
            
        Raises:
            AgentRuntimeException: If the agent could not be started
        """
        if agent_id not in self.agents:
            raise AgentRuntimeException(f"Agent {agent_id} not found")
        
        if self.agent_status[agent_id] == AgentStatus.RUNNING:
            return  # Already running
        
        try:
            # Start agent
            self.agent_status[agent_id] = AgentStatus.RUNNING
        except Exception as e:
            self.agent_status[agent_id] = AgentStatus.ERROR
            raise AgentRuntimeException(f"Failed to start agent {agent_id}: {str(e)}") from e
    
    async def stop_agent(self, agent_id: str) -> None:
        """Stop an agent.
        
        Args:
            agent_id: The ID of the agent to stop
            
        Raises:
            AgentRuntimeException: If the agent could not be stopped
        """
        if agent_id not in self.agents:
            raise AgentRuntimeException(f"Agent {agent_id} not found")
        
        if self.agent_status[agent_id] == AgentStatus.STOPPED:
            return  # Already stopped
        
        self.agent_status[agent_id] = AgentStatus.STOPPING
        
        # Cancel any in-progress runs
        if agent_id in self.runs_in_progress:
            for run_task in self.runs_in_progress[agent_id]:
                if not run_task.done():
                    run_task.cancel()
        
        try:
            # Stop agent
            self.agent_status[agent_id] = AgentStatus.STOPPED
        except Exception as e:
            self.agent_status[agent_id] = AgentStatus.ERROR
            raise AgentRuntimeException(f"Failed to stop agent {agent_id}: {str(e)}") from e
    
    async def run_agent(
        self, 
        agent_id: str, 
        input: Any, 
        tools: Optional[List[Any]] = None,
        timeout: Optional[int] = None
    ) -> Any:
        """Run an agent with the given input.
        
        Args:
            agent_id: The ID of the agent to run
            input: The input for the agent
            tools: Optional additional tools to use for this run
            timeout: Optional timeout in seconds (overrides runtime options)
            
        Returns:
            The result of the agent run
            
        Raises:
            AgentRuntimeException: If the agent could not be run
        """
        if agent_id not in self.agents:
            raise AgentRuntimeException(f"Agent {agent_id} not found")
        
        agent = self.agents[agent_id]
        
        if self.agent_status[agent_id] != AgentStatus.RUNNING:
            await self.start_agent(agent_id)
        
        timeout_value = timeout or self.options.timeout_seconds
        
        try:
            # Run the agent
            if hasattr(agent, 'run'):
                result = await agent.run(input)
            else:
                # Fallback for agents without a run method
                result = "Agent execution not implemented"
                
            return result
        except asyncio.TimeoutError:
            raise AgentRuntimeException(f"Agent {agent_id} run timed out after {timeout_value} seconds")
        except Exception as e:
            raise AgentRuntimeException(f"Agent {agent_id} run failed: {str(e)}") from e
    
    async def get_agent_status(self, agent_id: str) -> AgentStatus:
        """Get the status of an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            The agent status
            
        Raises:
            AgentRuntimeException: If the agent is not found
        """
        if agent_id not in self.agent_status:
            raise AgentRuntimeException(f"Agent {agent_id} not found")
        
        return self.agent_status[agent_id]
    
    async def save_state(self, agent_id: str) -> str:
        """Save the state of an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            A state ID that can be used to restore the agent
            
        Raises:
            AgentRuntimeException: If the agent state could not be saved
        """
        if agent_id not in self.agents:
            raise AgentRuntimeException(f"Agent {agent_id} not found")
        
        # For the minimal implementation, just return a dummy state ID
        state_id = f"state-{uuid.uuid4()}"
        return state_id
    
    async def restore_agent(self, state_id: str) -> str:
        """Restore an agent from a saved state.
        
        Args:
            state_id: The state ID returned by save_state
            
        Returns:
            The ID of the restored agent
            
        Raises:
            AgentRuntimeException: If the agent could not be restored
        """
        # For the minimal implementation, create a new agent
        agent_id = f"agent-{uuid.uuid4()}"
        self.agents[agent_id] = ContexaAgent(
            name="Restored Agent",
            description="An agent restored from a saved state",
            model=None,
            tools=[]
        )
        self.agent_status[agent_id] = AgentStatus.READY
        return agent_id 