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
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union
import uuid

from contexa_sdk.runtime.state_management import AgentState, StateProvider
from contexa_sdk.runtime.resource_tracking import ResourceUsage, ResourceLimits
from contexa_sdk.runtime.health_monitoring import HealthStatus, HealthCheck


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