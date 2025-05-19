"""Health monitoring for agent runtime environments.

This module provides interfaces and implementations for monitoring the health
of agents and runtime environments, and provides mechanisms for detecting and
recovering from failures.
"""

import abc
import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, Awaitable

from contexa_sdk.runtime.resource_tracking import ResourceLimits, ResourceUsage


class HealthStatus(str, Enum):
    """Health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.timestamp is None:
            self.timestamp = time.time()


class HealthCheck(abc.ABC):
    """Interface for a health check.
    
    A health check is responsible for checking the health of an agent or
    runtime environment component and returning a health status.
    """
    
    def __init__(self, name: str, description: str):
        """Initialize a health check.
        
        Args:
            name: Name of the health check
            description: Description of what the health check does
        """
        self.name = name
        self.description = description
    
    @abc.abstractmethod
    async def check_health(self, context: Dict[str, Any]) -> HealthCheckResult:
        """Check the health of a component.
        
        Args:
            context: Context information for the health check
            
        Returns:
            Result of the health check
        """
        pass
    
    @abc.abstractmethod
    async def attempt_recovery(self, context: Dict[str, Any]) -> bool:
        """Attempt to recover from an unhealthy state.
        
        Args:
            context: Context information for the recovery attempt
            
        Returns:
            True if recovery was successful, False otherwise
        """
        pass


class ResourceHealthCheck(HealthCheck):
    """Health check that monitors resource usage.
    
    This health check monitors resource usage against defined limits
    and reports health status based on how close the usage is to the limits.
    """
    
    def __init__(
        self,
        warning_threshold: float = 0.8,
        critical_threshold: float = 0.95
    ):
        """Initialize a resource health check.
        
        Args:
            warning_threshold: Threshold (as a fraction of the limit) at which
                to report a DEGRADED health status
            critical_threshold: Threshold (as a fraction of the limit) at which
                to report a CRITICAL health status
        """
        super().__init__(
            "Resource Health",
            "Checks resource usage against defined limits"
        )
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
    
    async def check_health(self, context: Dict[str, Any]) -> HealthCheckResult:
        """Check resource health based on usage and limits.
        
        Args:
            context: Context with 'usage' (ResourceUsage) and 'limits' (ResourceLimits)
            
        Returns:
            Result of the health check
        """
        if 'usage' not in context or 'limits' not in context:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message="Missing usage or limits information in context",
            )
        
        usage: ResourceUsage = context['usage']
        limits: ResourceLimits = context['limits']
        
        # Calculate resource utilization as a fraction of limits
        utilization = {}
        
        if limits.max_memory_mb != float('inf'):
            utilization['memory'] = usage.memory_mb / limits.max_memory_mb
        
        if limits.max_cpu_percent != float('inf'):
            utilization['cpu'] = usage.cpu_percent / limits.max_cpu_percent
        
        if limits.max_requests_per_minute != float('inf'):
            utilization['requests'] = (
                usage.requests_per_minute / limits.max_requests_per_minute
            )
        
        if (limits.max_tokens_per_minute is not None and 
                usage.tokens_per_minute is not None):
            utilization['tokens'] = (
                usage.tokens_per_minute / limits.max_tokens_per_minute
            )
        
        if (limits.max_concurrent_requests is not None and 
                usage.concurrent_requests > 0):
            utilization['concurrent_requests'] = (
                usage.concurrent_requests / limits.max_concurrent_requests
            )
        
        # Check for limit violations
        violations = []
        max_utilization = 0.0
        
        for resource, util in utilization.items():
            max_utilization = max(max_utilization, util)
            
            if util >= self.critical_threshold:
                violations.append(
                    f"{resource.capitalize()} at {util:.1%} of limit "
                    f"(critical threshold: {self.critical_threshold:.1%})"
                )
            elif util >= self.warning_threshold:
                violations.append(
                    f"{resource.capitalize()} at {util:.1%} of limit "
                    f"(warning threshold: {self.warning_threshold:.1%})"
                )
        
        # Determine overall health status
        if violations and max_utilization >= self.critical_threshold:
            status = HealthStatus.CRITICAL
            message = "Critical resource limit violations detected"
        elif violations and max_utilization >= self.warning_threshold:
            status = HealthStatus.DEGRADED
            message = "Resource usage approaching limits"
        elif utilization:
            status = HealthStatus.HEALTHY
            message = "Resource usage within acceptable limits"
        else:
            status = HealthStatus.UNKNOWN
            message = "No resource utilization data available"
        
        return HealthCheckResult(
            status=status,
            message=message,
            details={
                'utilization': utilization,
                'violations': violations,
                'warning_threshold': self.warning_threshold,
                'critical_threshold': self.critical_threshold,
            }
        )
    
    async def attempt_recovery(self, context: Dict[str, Any]) -> bool:
        """Attempt to recover from resource-related issues.
        
        This method doesn't directly recover resources but provides
        guidance for potential recovery actions. In a real implementation,
        this might trigger resource cleanup, restart, or scaling actions.
        
        Args:
            context: Context information for the recovery attempt
            
        Returns:
            True if recovery was successful, False otherwise
        """
        # Resource health checks typically can't automatically recover
        # Instead, they might trigger actions like scaling or cleanup
        return False


class ResponseTimeHealthCheck(HealthCheck):
    """Health check that monitors agent response times.
    
    This health check tracks how long agents take to respond to requests
    and reports health status based on response time thresholds.
    """
    
    def __init__(
        self,
        warning_threshold_ms: float = 2000.0,
        critical_threshold_ms: float = 5000.0,
        history_size: int = 10
    ):
        """Initialize a response time health check.
        
        Args:
            warning_threshold_ms: Response time threshold in milliseconds for
                reporting a DEGRADED health status
            critical_threshold_ms: Response time threshold in milliseconds for
                reporting a CRITICAL health status
            history_size: Number of recent response times to track
        """
        super().__init__(
            "Response Time",
            "Monitors agent response times against thresholds"
        )
        self.warning_threshold_ms = warning_threshold_ms
        self.critical_threshold_ms = critical_threshold_ms
        self.history_size = history_size
        self._response_times: Dict[str, List[float]] = {}
        self._lock = threading.RLock()
    
    def record_response_time(self, agent_id: str, response_time_ms: float) -> None:
        """Record a response time for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            response_time_ms: Response time in milliseconds
        """
        with self._lock:
            if agent_id not in self._response_times:
                self._response_times[agent_id] = []
            
            times = self._response_times[agent_id]
            times.append(response_time_ms)
            
            # Keep only the most recent response times
            if len(times) > self.history_size:
                self._response_times[agent_id] = times[-self.history_size:]
    
    async def check_health(self, context: Dict[str, Any]) -> HealthCheckResult:
        """Check health based on response times.
        
        Args:
            context: Context with 'agent_id' to check
            
        Returns:
            Result of the health check
        """
        if 'agent_id' not in context:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message="Missing agent_id in context",
            )
        
        agent_id = context['agent_id']
        
        with self._lock:
            if agent_id not in self._response_times or not self._response_times[agent_id]:
                return HealthCheckResult(
                    status=HealthStatus.UNKNOWN,
                    message=f"No response time data available for agent {agent_id}",
                )
            
            # Calculate average response time
            response_times = self._response_times[agent_id]
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # Determine health status based on average response time
            details = {
                'average_response_time_ms': avg_response_time,
                'max_response_time_ms': max_response_time,
                'recent_response_times_ms': response_times,
                'warning_threshold_ms': self.warning_threshold_ms,
                'critical_threshold_ms': self.critical_threshold_ms,
            }
            
            if avg_response_time > self.critical_threshold_ms:
                return HealthCheckResult(
                    status=HealthStatus.CRITICAL,
                    message=(
                        f"Critical: Average response time ({avg_response_time:.2f} ms) "
                        f"exceeds critical threshold ({self.critical_threshold_ms} ms)"
                    ),
                    details=details,
                )
            elif avg_response_time > self.warning_threshold_ms:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    message=(
                        f"Warning: Average response time ({avg_response_time:.2f} ms) "
                        f"exceeds warning threshold ({self.warning_threshold_ms} ms)"
                    ),
                    details=details,
                )
            else:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message=(
                        f"Healthy: Average response time ({avg_response_time:.2f} ms) "
                        f"within acceptable limits"
                    ),
                    details=details,
                )
    
    async def attempt_recovery(self, context: Dict[str, Any]) -> bool:
        """Attempt to recover from response time issues.
        
        Args:
            context: Context information for the recovery attempt
            
        Returns:
            True if recovery was successful, False otherwise
        """
        # Response time issues typically require investigation
        # This method could trigger diagnostics or resource reallocation
        return False


class HealthMonitor:
    """Monitors the health of agents and runtime components.
    
    This class coordinates running multiple health checks and aggregating
    the results to determine overall health status.
    """
    
    def __init__(self, check_interval_seconds: float = 60.0):
        """Initialize a health monitor.
        
        Args:
            check_interval_seconds: Interval at which to run health checks
        """
        self._health_checks: Dict[str, HealthCheck] = {}
        self._check_interval = check_interval_seconds
        self._last_check: Dict[str, Dict[str, float]] = {}
        self._health_status: Dict[str, Dict[str, HealthCheckResult]] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def register_health_check(self, health_check: HealthCheck) -> None:
        """Register a health check with the monitor.
        
        Args:
            health_check: Health check to register
        """
        with self._lock:
            self._health_checks[health_check.name] = health_check
    
    def unregister_health_check(self, check_name: str) -> None:
        """Unregister a health check from the monitor.
        
        Args:
            check_name: Name of the health check to unregister
        """
        with self._lock:
            if check_name in self._health_checks:
                del self._health_checks[check_name]
    
    async def check_health(
        self, 
        entity_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks for an entity.
        
        Args:
            entity_id: Identifier for the entity to check (e.g., agent ID)
            context: Context information for the health checks
            
        Returns:
            Dictionary mapping health check names to results
        """
        current_time = time.time()
        results = {}
        
        # Add entity_id to the context if not present
        check_context = context.copy()
        if 'entity_id' not in check_context:
            check_context['entity_id'] = entity_id
        
        # Run each health check
        for check_name, health_check in self._health_checks.items():
            # Check if we need to run this check (based on interval)
            with self._lock:
                last_check_time = (
                    self._last_check.get(entity_id, {}).get(check_name, 0)
                )
                
                if current_time - last_check_time < self._check_interval:
                    # Use cached result if available
                    if (entity_id in self._health_status and 
                            check_name in self._health_status[entity_id]):
                        results[check_name] = self._health_status[entity_id][check_name]
                        continue
            
            # Run the health check
            try:
                result = await health_check.check_health(check_context)
                
                # If the health is not HEALTHY, attempt recovery if needed
                if (result.status not in (HealthStatus.HEALTHY, HealthStatus.UNKNOWN) and 
                        not result.recovery_attempted):
                    self._logger.info(
                        f"Attempting recovery for {entity_id} from {check_name} health check"
                    )
                    result.recovery_attempted = True
                    result.recovery_successful = await health_check.attempt_recovery(check_context)
                    
                    if result.recovery_successful:
                        # Re-check health after recovery
                        result = await health_check.check_health(check_context)
                        self._logger.info(f"Recovery successful for {entity_id}")
                    else:
                        self._logger.warning(f"Recovery failed for {entity_id}")
                
                # Store the result
                with self._lock:
                    if entity_id not in self._health_status:
                        self._health_status[entity_id] = {}
                    if entity_id not in self._last_check:
                        self._last_check[entity_id] = {}
                    
                    self._health_status[entity_id][check_name] = result
                    self._last_check[entity_id][check_name] = current_time
                
                results[check_name] = result
                
            except Exception as e:
                # Handle exceptions during health checks
                self._logger.error(
                    f"Error running health check {check_name} for {entity_id}: {str(e)}"
                )
                results[check_name] = HealthCheckResult(
                    status=HealthStatus.UNKNOWN,
                    message=f"Error running health check: {str(e)}",
                )
        
        return results
    
    def get_overall_health(self, entity_id: str) -> HealthStatus:
        """Get the overall health status for an entity.
        
        This method aggregates the results of all health checks for an entity
        and returns the worst health status.
        
        Args:
            entity_id: Identifier for the entity
            
        Returns:
            Overall health status for the entity
        """
        with self._lock:
            if entity_id not in self._health_status:
                return HealthStatus.UNKNOWN
            
            # Find the worst health status
            status_priority = {
                HealthStatus.HEALTHY: 0,
                HealthStatus.UNKNOWN: 1,
                HealthStatus.DEGRADED: 2,
                HealthStatus.UNHEALTHY: 3,
                HealthStatus.CRITICAL: 4,
            }
            
            worst_status = HealthStatus.HEALTHY
            for result in self._health_status[entity_id].values():
                if status_priority[result.status] > status_priority[worst_status]:
                    worst_status = result.status
            
            return worst_status
    
    def get_health_details(self, entity_id: str) -> Dict[str, Any]:
        """Get detailed health information for an entity.
        
        Args:
            entity_id: Identifier for the entity
            
        Returns:
            Dictionary with detailed health information
        """
        with self._lock:
            if entity_id not in self._health_status:
                return {"status": HealthStatus.UNKNOWN.name, "details": {}}
            
            overall_status = self.get_overall_health(entity_id)
            check_results = {}
            
            for check_name, result in self._health_status[entity_id].items():
                check_results[check_name] = {
                    "status": result.status.name,
                    "message": result.message,
                    "timestamp": result.timestamp,
                    "details": result.details,
                    "recovery_attempted": result.recovery_attempted,
                    "recovery_successful": result.recovery_successful,
                }
            
            return {
                "status": overall_status.name,
                "checks": check_results,
            }
            
    def clear_health_data(self, entity_id: str) -> None:
        """Clear health data for an entity.
        
        Args:
            entity_id: Identifier for the entity
        """
        with self._lock:
            if entity_id in self._health_status:
                del self._health_status[entity_id]
            if entity_id in self._last_check:
                del self._last_check[entity_id] 