"""Resource tracking for agent runtime environments.

This module provides interfaces and implementations for tracking and
limiting agent resource usage, such as memory, CPU, and request rate.
"""

import asyncio
import dataclasses
import logging
import os
import platform
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class ResourceLimits:
    """Resource limits for an agent."""
    # Maximum memory usage in MB
    max_memory_mb: float = float('inf')
    
    # Maximum CPU usage as a percentage (0-100)
    max_cpu_percent: float = float('inf')
    
    # Maximum requests per minute
    max_requests_per_minute: float = float('inf')
    
    # Maximum tokens per minute (for LLM-based agents)
    max_tokens_per_minute: Optional[int] = None
    
    # Maximum concurrent requests
    max_concurrent_requests: Optional[int] = None
    
    # Additional limits as key-value pairs
    additional_limits: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceUsage:
    """Resource usage information for an agent."""
    # Agent ID
    agent_id: str
    
    # Current memory usage in MB
    memory_mb: float = 0.0
    
    # Current CPU usage as a percentage (0-100)
    cpu_percent: float = 0.0
    
    # Requests per minute
    requests_per_minute: float = 0.0
    
    # Tokens per minute (for LLM-based agents)
    tokens_per_minute: Optional[int] = None
    
    # Current concurrent requests
    concurrent_requests: int = 0
    
    # Last updated timestamp
    last_updated: float = field(default_factory=time.time)
    
    # Request count within the current minute
    _request_count: int = 0
    
    # Token count within the current minute
    _token_count: int = 0
    
    # Minute window start time
    _minute_start: float = field(default_factory=time.time)
    
    # Additional usage metrics as key-value pairs
    additional_usage: Dict[str, Any] = field(default_factory=dict)
    
    def record_request(self) -> None:
        """Record a new request."""
        current_time = time.time()
        self.concurrent_requests += 1
        
        # Reset counters if we've moved to a new minute
        if current_time - self._minute_start >= 60:
            # Calculate requests per minute before resetting
            elapsed_minutes = (current_time - self._minute_start) / 60
            if elapsed_minutes > 0:
                self.requests_per_minute = self._request_count / elapsed_minutes
                if self._token_count > 0:
                    self.tokens_per_minute = int(self._token_count / elapsed_minutes)
            
            # Reset for the new minute window
            self._request_count = 0
            self._token_count = 0
            self._minute_start = current_time
        
        self._request_count += 1
        self.last_updated = current_time
    
    def record_request_completed(self) -> None:
        """Record a request completion."""
        self.concurrent_requests = max(0, self.concurrent_requests - 1)
        self.last_updated = time.time()
    
    def record_tokens(self, token_count: int) -> None:
        """Record token usage.
        
        Args:
            token_count: Number of tokens to record
        """
        current_time = time.time()
        
        # Reset counters if we've moved to a new minute
        if current_time - self._minute_start >= 60:
            # Calculate tokens per minute before resetting
            elapsed_minutes = (current_time - self._minute_start) / 60
            if elapsed_minutes > 0:
                self.requests_per_minute = self._request_count / elapsed_minutes
                if self._token_count > 0:
                    self.tokens_per_minute = int(self._token_count / elapsed_minutes)
            
            # Reset for the new minute window
            self._request_count = 0
            self._token_count = 0
            self._minute_start = current_time
        
        self._token_count += token_count
        self.last_updated = current_time
    
    def update_system_metrics(self) -> None:
        """Update system metrics like memory and CPU usage.
        
        This method attempts to use psutil if available. If not,
        it will leave the values unchanged.
        """
        if not PSUTIL_AVAILABLE:
            return
        
        current_process = psutil.Process(os.getpid())
        
        # Get memory info in MB
        memory_info = current_process.memory_info()
        self.memory_mb = memory_info.rss / (1024 * 1024)
        
        # Get CPU usage
        self.cpu_percent = current_process.cpu_percent(interval=0.1)
        
        self.last_updated = time.time()
    
    def check_limits(self, limits: ResourceLimits) -> List[str]:
        """Check if any resource limits are being exceeded.
        
        Args:
            limits: Resource limits to check against
            
        Returns:
            List of violated limit descriptions, empty if no limits exceeded
        """
        violations = []
        
        if self.memory_mb > limits.max_memory_mb:
            violations.append(
                f"Memory usage ({self.memory_mb:.2f} MB) exceeds limit "
                f"({limits.max_memory_mb:.2f} MB)"
            )
        
        if self.cpu_percent > limits.max_cpu_percent:
            violations.append(
                f"CPU usage ({self.cpu_percent:.2f}%) exceeds limit "
                f"({limits.max_cpu_percent:.2f}%)"
            )
        
        if self.requests_per_minute > limits.max_requests_per_minute:
            violations.append(
                f"Request rate ({self.requests_per_minute:.2f} rpm) exceeds limit "
                f"({limits.max_requests_per_minute:.2f} rpm)"
            )
        
        if (limits.max_tokens_per_minute is not None and 
                self.tokens_per_minute is not None and 
                self.tokens_per_minute > limits.max_tokens_per_minute):
            violations.append(
                f"Token rate ({self.tokens_per_minute} tpm) exceeds limit "
                f"({limits.max_tokens_per_minute} tpm)"
            )
        
        if (limits.max_concurrent_requests is not None and 
                self.concurrent_requests > limits.max_concurrent_requests):
            violations.append(
                f"Concurrent requests ({self.concurrent_requests}) exceeds limit "
                f"({limits.max_concurrent_requests})"
            )
        
        # Check additional limits
        for key, limit_value in limits.additional_limits.items():
            if key in self.additional_usage and self.additional_usage[key] > limit_value:
                violations.append(
                    f"{key} ({self.additional_usage[key]}) exceeds limit "
                    f"({limit_value})"
                )
        
        return violations


class ResourceTracker:
    """Tracks resource usage for multiple agents.
    
    This class provides methods for tracking and enforcing resource limits
    for agents running in a runtime environment.
    """
    
    def __init__(self, update_interval_seconds: float = 5.0):
        """Initialize a resource tracker.
        
        Args:
            update_interval_seconds: Interval at which to update system metrics
        """
        self._resources: Dict[str, ResourceUsage] = {}
        self._limits: Dict[str, ResourceLimits] = {}
        self._lock = threading.RLock()
        self._update_interval = update_interval_seconds
        self._last_system_update: Dict[str, float] = {}
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def register_agent(
        self, 
        agent_id: str, 
        limits: Optional[ResourceLimits] = None
    ) -> None:
        """Register an agent for resource tracking.
        
        Args:
            agent_id: Unique identifier for the agent
            limits: Resource limits for the agent
        """
        with self._lock:
            self._resources[agent_id] = ResourceUsage(agent_id=agent_id)
            if limits:
                self._limits[agent_id] = limits
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from resource tracking.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        with self._lock:
            if agent_id in self._resources:
                del self._resources[agent_id]
            if agent_id in self._limits:
                del self._limits[agent_id]
            if agent_id in self._last_system_update:
                del self._last_system_update[agent_id]
    
    def set_limits(self, agent_id: str, limits: ResourceLimits) -> None:
        """Set resource limits for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            limits: Resource limits for the agent
        """
        with self._lock:
            self._limits[agent_id] = limits
    
    def get_limits(self, agent_id: str) -> Optional[ResourceLimits]:
        """Get resource limits for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Resource limits for the agent, or None if no limits are set
        """
        with self._lock:
            return self._limits.get(agent_id)
    
    def record_request(self, agent_id: str) -> None:
        """Record a new request for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        with self._lock:
            if agent_id in self._resources:
                self._resources[agent_id].record_request()
                self._maybe_update_system_metrics(agent_id)
    
    def record_request_completed(self, agent_id: str) -> None:
        """Record a request completion for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        with self._lock:
            if agent_id in self._resources:
                self._resources[agent_id].record_request_completed()
    
    def record_tokens(self, agent_id: str, token_count: int) -> None:
        """Record token usage for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            token_count: Number of tokens to record
        """
        with self._lock:
            if agent_id in self._resources:
                self._resources[agent_id].record_tokens(token_count)
    
    def get_usage(self, agent_id: str) -> Optional[ResourceUsage]:
        """Get resource usage for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Resource usage for the agent, or None if the agent is not registered
        """
        with self._lock:
            if agent_id in self._resources:
                self._maybe_update_system_metrics(agent_id)
                return self._resources[agent_id]
            return None
    
    def check_limits(self, agent_id: str) -> List[str]:
        """Check if an agent is exceeding any resource limits.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            List of violated limit descriptions, empty if no limits exceeded
        """
        with self._lock:
            if agent_id not in self._resources:
                return []
            
            # Update system metrics before checking limits
            self._maybe_update_system_metrics(agent_id)
            
            # Check against agent-specific limits if they exist
            if agent_id in self._limits:
                return self._resources[agent_id].check_limits(self._limits[agent_id])
            
            return []
    
    def _maybe_update_system_metrics(self, agent_id: str) -> None:
        """Update system metrics if the update interval has elapsed.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        current_time = time.time()
        last_update = self._last_system_update.get(agent_id, 0)
        
        if current_time - last_update >= self._update_interval:
            self._resources[agent_id].update_system_metrics()
            self._last_system_update[agent_id] = current_time 