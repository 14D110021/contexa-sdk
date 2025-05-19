"""Resource tracking module for monitoring and limiting agent resource usage."""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass


class ResourceType(str, Enum):
    """Types of resources that can be tracked."""
    MEMORY = "memory"
    CPU = "cpu"
    TOKENS = "tokens"
    REQUESTS = "requests"
    STORAGE = "storage"
    BANDWIDTH = "bandwidth"
    CUSTOM = "custom"


@dataclass
class ResourceUsage:
    """Resource usage data."""
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    tokens_used: int = 0
    tokens_used_last_minute: int = 0
    requests_per_minute: int = 0
    bandwidth_kb: float = 0.0
    custom_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_metrics is None:
            self.custom_metrics = {}


@dataclass
class ResourceLimits:
    """Resource limits for an agent."""
    max_memory_mb: Optional[float] = None
    max_cpu_percent: Optional[float] = None
    max_tokens: Optional[int] = None
    max_tokens_per_minute: Optional[int] = None
    max_requests_per_minute: Optional[int] = None
    max_bandwidth_kb: Optional[float] = None
    custom_limits: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_limits is None:
            self.custom_limits = {}


class ResourceConstraintViolation(Exception):
    """Exception raised when a resource constraint is violated."""
    
    def __init__(
        self, 
        resource_type: ResourceType, 
        current_value: Any, 
        limit_value: Any, 
        agent_id: Optional[str] = None
    ):
        """Initialize a resource constraint violation.
        
        Args:
            resource_type: The type of resource that exceeded its limit
            current_value: The current value of the resource
            limit_value: The limit value that was exceeded
            agent_id: Optional ID of the agent that exceeded the limit
        """
        self.resource_type = resource_type
        self.current_value = current_value
        self.limit_value = limit_value
        self.agent_id = agent_id
        
        message = (
            f"Resource constraint violated: {resource_type.value} "
            f"({current_value} > {limit_value})"
        )
        
        if agent_id:
            message += f" for agent {agent_id}"
            
        super().__init__(message)


class ResourceTracker:
    """Tracks and limits resource usage for agents.
    
    The ResourceTracker monitors resource usage for agents and enforces
    resource limits. It can track:
    - Memory usage
    - CPU usage
    - Token usage (for LLM calls)
    - Request rates
    - Bandwidth usage
    - Custom metrics
    """
    
    def __init__(self):
        """Initialize the resource tracker."""
        self.agent_usage: Dict[str, ResourceUsage] = {}
        self.agent_limits: Dict[str, ResourceLimits] = {}
    
    def register_agent(self, agent_id: str, limits: Optional[ResourceLimits] = None) -> None:
        """Register an agent for resource tracking.
        
        Args:
            agent_id: The ID of the agent to track
            limits: Optional resource limits for the agent
        """
        self.agent_usage[agent_id] = ResourceUsage()
        self.agent_limits[agent_id] = limits or ResourceLimits()
    
    def update_usage(self, agent_id: str, resource_usage: ResourceUsage) -> None:
        """Update resource usage for an agent.
        
        Args:
            agent_id: The ID of the agent
            resource_usage: The updated resource usage
            
        Raises:
            ResourceConstraintViolation: If a resource limit is exceeded
        """
        if agent_id not in self.agent_usage:
            self.register_agent(agent_id)
            
        self.agent_usage[agent_id] = resource_usage
        
        # Check limits
        limits = self.agent_limits.get(agent_id)
        if limits:
            self._check_limits(agent_id, resource_usage, limits)
    
    def get_usage(self, agent_id: str) -> ResourceUsage:
        """Get current resource usage for an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            The current resource usage
            
        Raises:
            ValueError: If the agent is not registered
        """
        if agent_id not in self.agent_usage:
            raise ValueError(f"Agent {agent_id} not registered for resource tracking")
            
        return self.agent_usage[agent_id]
    
    def set_limits(self, agent_id: str, limits: ResourceLimits) -> None:
        """Set resource limits for an agent.
        
        Args:
            agent_id: The ID of the agent
            limits: The resource limits to set
        """
        if agent_id not in self.agent_limits:
            self.register_agent(agent_id, limits)
        else:
            self.agent_limits[agent_id] = limits
    
    def get_limits(self, agent_id: str) -> ResourceLimits:
        """Get current resource limits for an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            The current resource limits
            
        Raises:
            ValueError: If the agent is not registered
        """
        if agent_id not in self.agent_limits:
            raise ValueError(f"Agent {agent_id} not registered for resource tracking")
            
        return self.agent_limits[agent_id]
    
    def _check_limits(self, agent_id: str, usage: ResourceUsage, limits: ResourceLimits) -> None:
        """Check if resource usage exceeds limits.
        
        Args:
            agent_id: The ID of the agent
            usage: The current resource usage
            limits: The resource limits to check
            
        Raises:
            ResourceConstraintViolation: If a resource limit is exceeded
        """
        # Check memory limit
        if limits.max_memory_mb is not None and usage.memory_mb > limits.max_memory_mb:
            raise ResourceConstraintViolation(
                ResourceType.MEMORY,
                usage.memory_mb,
                limits.max_memory_mb,
                agent_id
            )
            
        # Check CPU limit
        if limits.max_cpu_percent is not None and usage.cpu_percent > limits.max_cpu_percent:
            raise ResourceConstraintViolation(
                ResourceType.CPU,
                usage.cpu_percent,
                limits.max_cpu_percent,
                agent_id
            )
            
        # Check token limit
        if limits.max_tokens is not None and usage.tokens_used > limits.max_tokens:
            raise ResourceConstraintViolation(
                ResourceType.TOKENS,
                usage.tokens_used,
                limits.max_tokens,
                agent_id
            )
            
        # Check token rate limit
        if (limits.max_tokens_per_minute is not None and 
                usage.tokens_used_last_minute > limits.max_tokens_per_minute):
            raise ResourceConstraintViolation(
                ResourceType.TOKENS,
                usage.tokens_used_last_minute,
                limits.max_tokens_per_minute,
                agent_id
            )
            
        # Check request rate limit
        if (limits.max_requests_per_minute is not None and 
                usage.requests_per_minute > limits.max_requests_per_minute):
            raise ResourceConstraintViolation(
                ResourceType.REQUESTS,
                usage.requests_per_minute,
                limits.max_requests_per_minute,
                agent_id
            )
            
        # Check bandwidth limit
        if limits.max_bandwidth_kb is not None and usage.bandwidth_kb > limits.max_bandwidth_kb:
            raise ResourceConstraintViolation(
                ResourceType.BANDWIDTH,
                usage.bandwidth_kb,
                limits.max_bandwidth_kb,
                agent_id
            )
            
        # Check custom limits
        for metric, limit in limits.custom_limits.items():
            if metric in usage.custom_metrics and usage.custom_metrics[metric] > limit:
                raise ResourceConstraintViolation(
                    ResourceType.CUSTOM,
                    usage.custom_metrics[metric],
                    limit,
                    agent_id
                ) 