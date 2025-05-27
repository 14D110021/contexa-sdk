"""Resource tracking module for monitoring and limiting agent resource usage.

This module provides tools to track and limit resource consumption by agents,
ensuring they operate within defined constraints and prevent resource exhaustion.
"""

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
    resource limits to prevent resource exhaustion and ensure fair resource
    allocation in multi-agent environments. It supports tracking various
    resource types including:
    
    - Memory usage (RAM consumption)
    - CPU usage (processor utilization)
    - Token usage (for LLM API calls)
    - Request rates (API call frequency)
    - Bandwidth usage (network traffic)
    - Custom metrics (user-defined resources)
    
    This class provides methods to register agents, update and retrieve their
    resource usage, set and enforce resource limits, and handle constraint
    violations with appropriate exceptions.
    
    Attributes:
        agent_usage: Dictionary mapping agent IDs to their ResourceUsage
        agent_limits: Dictionary mapping agent IDs to their ResourceLimits
    """
    
    def __init__(self):
        """Initialize the resource tracker with empty tracking dictionaries."""
        self.agent_usage: Dict[str, ResourceUsage] = {}
        self.agent_limits: Dict[str, ResourceLimits] = {}
    
    def register_agent(self, agent_id: str, limits: Optional[ResourceLimits] = None) -> None:
        """Register an agent for resource tracking.
        
        Adds an agent to the resource tracking system with optional resource limits.
        If no limits are provided, default unlimited resources are assumed. This method
        must be called before updating or retrieving resource usage for an agent.
        
        Args:
            agent_id: The unique identifier of the agent to track
            limits: Optional resource limits for the agent. If None, default
                unlimited ResourceLimits will be used.
        """
        self.agent_usage[agent_id] = ResourceUsage()
        self.agent_limits[agent_id] = limits or ResourceLimits()
    
    def update_usage(self, agent_id: str, resource_usage: ResourceUsage) -> None:
        """Update resource usage for an agent and check against limits.
        
        Updates the recorded resource usage for an agent and checks if any
        resource limits have been exceeded. If the agent is not yet registered,
        it will be automatically registered with default limits.
        
        Args:
            agent_id: The unique identifier of the agent
            resource_usage: The updated resource usage metrics to record
            
        Raises:
            ResourceConstraintViolation: If any resource limit is exceeded.
                This exception includes details about which resource was exceeded,
                the current value, and the limit value.
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
        
        Retrieves the most recently recorded resource usage metrics for
        the specified agent.
        
        Args:
            agent_id: The unique identifier of the agent
            
        Returns:
            The current ResourceUsage object containing all tracked metrics
            
        Raises:
            ValueError: If the agent is not registered for resource tracking
        """
        if agent_id not in self.agent_usage:
            raise ValueError(f"Agent {agent_id} not registered for resource tracking")
            
        return self.agent_usage[agent_id]
    
    def set_limits(self, agent_id: str, limits: ResourceLimits) -> None:
        """Set or update resource limits for an agent.
        
        Establishes resource constraints for an agent. These limits will be
        enforced when resource usage is updated. If the agent is not yet
        registered, it will be automatically registered.
        
        Args:
            agent_id: The unique identifier of the agent
            limits: The ResourceLimits object defining the constraints for
                each tracked resource type
        """
        if agent_id not in self.agent_limits:
            self.register_agent(agent_id, limits)
        else:
            self.agent_limits[agent_id] = limits
    
    def get_limits(self, agent_id: str) -> ResourceLimits:
        """Get current resource limits for an agent.
        
        Retrieves the current resource limits configured for the specified agent.
        
        Args:
            agent_id: The unique identifier of the agent
            
        Returns:
            The current ResourceLimits object containing all resource constraints
            
        Raises:
            ValueError: If the agent is not registered for resource tracking
        """
        if agent_id not in self.agent_limits:
            raise ValueError(f"Agent {agent_id} not registered for resource tracking")
            
        return self.agent_limits[agent_id]
    
    def _check_limits(self, agent_id: str, usage: ResourceUsage, limits: ResourceLimits) -> None:
        """Check if resource usage exceeds limits and raise exceptions if needed.
        
        Internal method that compares current resource usage against defined limits
        and raises appropriate exceptions when limits are exceeded.
        
        Args:
            agent_id: The unique identifier of the agent
            usage: The current resource usage metrics to check
            limits: The resource limits to check against
            
        Raises:
            ResourceConstraintViolation: If any resource limit is exceeded.
                This provides details about which specific resource was exceeded,
                by how much, and what the limit was.
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