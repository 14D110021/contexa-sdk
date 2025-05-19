"""Integration tests for runtime components."""

import pytest
import asyncio
from typing import Dict, Any, List

from contexa_sdk.runtime.agent_runtime import AgentRuntime, AgentStatus, RuntimeOptions
from contexa_sdk.runtime.resource_tracking import (
    ResourceTracker, 
    ResourceUsage, 
    ResourceLimits, 
    ResourceType,
    ResourceConstraintViolation
)
from contexa_sdk.runtime.health_monitoring import (
    HealthMonitor,
    HealthStatus,
    HealthCheck,
    HealthCheckResult
)
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel, ModelMessage


class TestRuntimeIntegration:
    """Integration tests for runtime components working together."""
    
    @pytest.fixture
    async def runtime_setup(self):
        """Set up runtime components for testing."""
        # Create runtime components
        runtime = AgentRuntime(options=RuntimeOptions(telemetry_enabled=True))
        resource_tracker = ResourceTracker()
        health_monitor = HealthMonitor()
        
        # Create a mock agent
        model = ContexaModel(model_name="test-model", provider="test")
        agent = ContexaAgent(
            name="Test Agent",
            description="Test agent for integration tests",
            model=model,
            tools=[]
        )
        
        # Register agent with runtime
        agent_id = await runtime.register_agent(agent)
        
        # Register agent with resource tracker
        resource_tracker.register_agent(agent_id, ResourceLimits(
            max_memory_mb=1024,
            max_tokens_per_minute=1000
        ))
        
        # Create health check for the agent
        async def check_agent_health():
            status = await runtime.get_agent_status(agent_id)
            return status != AgentStatus.ERROR
            
        health_check = HealthCheck(
            name=f"agent_{agent_id}_health",
            check_fn=check_agent_health,
            description=f"Checks if agent {agent_id} is healthy"
        )
        
        health_monitor.register_check(health_check)
        
        # Return components
        return {
            "runtime": runtime,
            "resource_tracker": resource_tracker,
            "health_monitor": health_monitor,
            "agent_id": agent_id
        }
    
    @pytest.mark.asyncio
    async def test_agent_lifecycle_with_resources(self, runtime_setup):
        """Test agent lifecycle with resource tracking."""
        runtime = runtime_setup["runtime"]
        resource_tracker = runtime_setup["resource_tracker"]
        agent_id = runtime_setup["agent_id"]
        
        # Start the agent
        await runtime.start_agent(agent_id)
        
        # Get agent status
        status = await runtime.get_agent_status(agent_id)
        assert status == AgentStatus.RUNNING
        
        # Update resource usage
        resource_usage = ResourceUsage(
            memory_mb=100.0,
            tokens_used=500,
            tokens_used_last_minute=500
        )
        
        resource_tracker.update_usage(agent_id, resource_usage)
        
        # Get resource usage
        current_usage = resource_tracker.get_usage(agent_id)
        assert current_usage.memory_mb == 100.0
        assert current_usage.tokens_used == 500
        
        # Stop the agent
        await runtime.stop_agent(agent_id)
        
        # Get agent status again
        status = await runtime.get_agent_status(agent_id)
        assert status == AgentStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_resource_limit_enforcement(self, runtime_setup):
        """Test that resource limits are enforced."""
        resource_tracker = runtime_setup["resource_tracker"]
        agent_id = runtime_setup["agent_id"]
        
        # Set a low memory limit
        resource_tracker.set_limits(agent_id, ResourceLimits(
            max_memory_mb=100.0,
            max_tokens_per_minute=1000
        ))
        
        # Update with usage within limits
        resource_tracker.update_usage(agent_id, ResourceUsage(
            memory_mb=50.0,
            tokens_used_last_minute=500
        ))
        
        # Now exceed the limit
        with pytest.raises(ResourceConstraintViolation) as excinfo:
            resource_tracker.update_usage(agent_id, ResourceUsage(
                memory_mb=150.0,
                tokens_used_last_minute=500
            ))
        
        # Verify the exception details
        assert excinfo.value.resource_type == ResourceType.MEMORY
        assert excinfo.value.current_value == 150.0
        assert excinfo.value.limit_value == 100.0
        assert excinfo.value.agent_id == agent_id
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, runtime_setup):
        """Test health monitoring integration."""
        runtime = runtime_setup["runtime"]
        health_monitor = runtime_setup["health_monitor"]
        agent_id = runtime_setup["agent_id"]
        
        # Start the agent
        await runtime.start_agent(agent_id)
        
        # Run health check
        check_name = f"agent_{agent_id}_health"
        result = await health_monitor.run_check(check_name)
        
        # Verify result
        assert result.status == HealthStatus.HEALTHY
        
        # Simulate an error by updating agent status
        runtime.agent_status[agent_id] = AgentStatus.ERROR
        
        # Run health check again
        result = await health_monitor.run_check(check_name)
        
        # Verify result
        assert result.status == HealthStatus.DEGRADED 