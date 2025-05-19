"""Unit tests for the health monitoring module."""

import pytest
import unittest.mock as mock
import asyncio
from typing import Dict, Any, Callable, Awaitable

from contexa_sdk.runtime.health_monitoring import (
    HealthMonitor,
    HealthStatus,
    HealthCheck,
    HealthCheckResult,
    HealthRecoveryAction
)


class TestHealthMonitor:
    """Test the HealthMonitor class."""

    def test_init(self):
        """Test that HealthMonitor initializes correctly."""
        monitor = HealthMonitor()
        assert monitor is not None
        assert isinstance(monitor, HealthMonitor)
        assert len(monitor.health_checks) == 0
        assert len(monitor.recovery_actions) == 0
        assert len(monitor._monitored_agents) == 0
    
    def test_register_check(self):
        """Test registering a health check."""
        monitor = HealthMonitor()
        
        # Define a simple check function
        async def check_function() -> bool:
            return True
        
        # Register the check
        check_id = monitor.register_check(
            name="test_check",
            check_function=check_function,
            description="A test health check"
        )
        
        # Verify the check is registered
        assert check_id in monitor.health_checks
        assert monitor.health_checks[check_id].name == "test_check"
        assert monitor.health_checks[check_id].description == "A test health check"
        assert monitor.health_checks[check_id].check_function == check_function
    
    def test_register_recovery(self):
        """Test registering a recovery action."""
        monitor = HealthMonitor()
        
        # Define a simple recovery function
        async def recovery_function() -> bool:
            return True
        
        # Register a check first
        check_id = "check-123"
        monitor.health_checks[check_id] = HealthCheck(
            id=check_id,
            name="test_check",
            check_function=mock.AsyncMock(return_value=True),
            description="A test health check"
        )
        
        # Register the recovery action
        recovery_id = monitor.register_recovery(
            check_id=check_id,
            recovery_function=recovery_function,
            description="A test recovery action"
        )
        
        # Verify the recovery action is registered
        assert recovery_id in monitor.recovery_actions
        assert monitor.recovery_actions[recovery_id].check_id == check_id
        assert monitor.recovery_actions[recovery_id].description == "A test recovery action"
        assert monitor.recovery_actions[recovery_id].recovery_function == recovery_function
    
    @pytest.mark.asyncio
    async def test_run_health_check(self):
        """Test running a health check."""
        monitor = HealthMonitor()
        
        # Define and register a check function that returns True
        check_function = mock.AsyncMock(return_value=True)
        check_id = monitor.register_check(
            name="test_check",
            check_function=check_function,
            description="A test health check"
        )
        
        # Run the check
        result = await monitor.run_health_check(check_id)
        
        # Verify the check was run and returned the expected result
        assert result.status == HealthStatus.HEALTHY
        assert result.check_id == check_id
        check_function.assert_called_once()
        
        # Now test with a check that returns False
        check_function.reset_mock()
        check_function.return_value = False
        
        # Run the check
        result = await monitor.run_health_check(check_id)
        
        # Verify the check was run and returned the expected result
        assert result.status == HealthStatus.UNHEALTHY
        assert result.check_id == check_id
        check_function.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_recovery_action(self):
        """Test running a recovery action."""
        monitor = HealthMonitor()
        
        # Define and register a check function
        check_function = mock.AsyncMock(return_value=False)  # Unhealthy
        check_id = monitor.register_check(
            name="test_check",
            check_function=check_function,
            description="A test health check"
        )
        
        # Define and register a recovery function
        recovery_function = mock.AsyncMock(return_value=True)  # Success
        recovery_id = monitor.register_recovery(
            check_id=check_id,
            recovery_function=recovery_function,
            description="A test recovery action"
        )
        
        # Run the recovery action
        result = await monitor.run_recovery_action(recovery_id)
        
        # Verify the recovery action was run and returned the expected result
        assert result is True
        recovery_function.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_monitor_agent(self):
        """Test monitoring an agent."""
        monitor = HealthMonitor()
        
        # Define and register a check function
        check_function = mock.AsyncMock(return_value=True)
        check_id = monitor.register_check(
            name="test_check",
            check_function=check_function,
            description="A test health check"
        )
        
        # Mock the internal _schedule_agent_monitoring method
        with mock.patch.object(monitor, '_schedule_agent_monitoring') as mock_schedule:
            # Start monitoring an agent
            agent_id = "agent-123"
            await monitor.monitor_agent(
                agent_id=agent_id,
                check_ids=[check_id],
                interval_seconds=60
            )
            
            # Verify the agent is set up for monitoring
            assert agent_id in monitor._monitored_agents
            assert monitor._monitored_agents[agent_id].check_ids == [check_id]
            assert monitor._monitored_agents[agent_id].interval_seconds == 60
            
            # Verify the monitoring was scheduled
            mock_schedule.assert_called_once_with(agent_id)
    
    @pytest.mark.asyncio
    async def test_stop_monitoring_agent(self):
        """Test stopping agent monitoring."""
        monitor = HealthMonitor()
        
        # Mock an agent being monitored
        agent_id = "agent-123"
        monitor._monitored_agents[agent_id] = mock.MagicMock()
        monitor._monitoring_tasks[agent_id] = asyncio.create_task(asyncio.sleep(0))
        
        # Stop monitoring the agent
        await monitor.stop_monitoring_agent(agent_id)
        
        # Verify the agent is no longer being monitored
        assert agent_id not in monitor._monitored_agents
        assert agent_id not in monitor._monitoring_tasks
    
    @pytest.mark.asyncio
    async def test_get_agent_health(self):
        """Test getting an agent's health status."""
        monitor = HealthMonitor()
        
        # Define and register a check function
        check_function = mock.AsyncMock(return_value=True)
        check_id = monitor.register_check(
            name="test_check",
            check_function=check_function,
            description="A test health check"
        )
        
        # Define an agent ID
        agent_id = "agent-123"
        
        # Mock the run_health_check method
        with mock.patch.object(monitor, 'run_health_check') as mock_run_check:
            # Set up the mock to return a healthy result
            mock_run_check.return_value = HealthCheckResult(
                check_id=check_id,
                status=HealthStatus.HEALTHY,
                message="All good",
                timestamp="2023-01-01T00:00:00Z"
            )
            
            # Mock the agent being monitored with this check
            monitor._monitored_agents[agent_id] = mock.MagicMock(check_ids=[check_id])
            
            # Get the agent's health
            health = await monitor.get_agent_health(agent_id)
            
            # Verify the health check was run
            mock_run_check.assert_called_once_with(check_id)
            
            # Verify the health status
            assert len(health) == 1
            assert health[0].check_id == check_id
            assert health[0].status == HealthStatus.HEALTHY 