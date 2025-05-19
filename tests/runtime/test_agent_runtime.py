"""Unit tests for the agent runtime module."""

import pytest
import unittest.mock as mock
import asyncio
from typing import Dict, Any, List

from contexa_sdk.runtime.agent_runtime import (
    AgentRuntime, 
    AgentStatus, 
    RuntimeOptions, 
    AgentRuntimeException
)
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel, ModelMessage
from contexa_sdk.core.tool import ContexaTool


class TestAgentRuntime:
    """Test the AgentRuntime class."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        # Create a mock agent
        agent = mock.MagicMock(spec=ContexaAgent)
        agent.agent_id = "test-agent"
        agent.name = "Test Agent"
        agent.run = mock.AsyncMock(return_value="Test response")
        
        return agent
    
    def test_init(self):
        """Test that AgentRuntime initializes correctly."""
        runtime = AgentRuntime()
        assert runtime is not None
        assert isinstance(runtime, AgentRuntime)
        assert len(runtime._agents) == 0
        assert runtime._state_manager is not None
        assert runtime._resource_tracker is not None
        assert runtime._health_monitor is not None
    
    def test_runtime_options_init(self):
        """Test that RuntimeOptions initializes correctly."""
        options = RuntimeOptions(
            enable_state_persistence=True,
            enable_resource_tracking=True,
            enable_health_monitoring=True,
            enable_observability=True
        )
        assert options.enable_state_persistence is True
        assert options.enable_resource_tracking is True
        assert options.enable_health_monitoring is True
        assert options.enable_observability is True
    
    @pytest.mark.asyncio
    async def test_register_agent(self, mock_agent):
        """Test registering an agent with the runtime."""
        runtime = AgentRuntime()
        
        # Mock the internal methods
        with mock.patch.object(runtime, '_setup_state_persistence') as mock_state, \
             mock.patch.object(runtime, '_setup_resource_tracking') as mock_resource, \
             mock.patch.object(runtime, '_setup_health_monitoring') as mock_health:
            
            # Register the agent
            options = RuntimeOptions(
                enable_state_persistence=True,
                enable_resource_tracking=True,
                enable_health_monitoring=True
            )
            
            agent_id = await runtime.register_agent(mock_agent, options)
            
            # Verify the agent is registered
            assert agent_id in runtime._agents
            assert runtime._agents[agent_id].status == AgentStatus.REGISTERED
            
            # Verify the setup methods were called
            mock_state.assert_called_once_with(agent_id)
            mock_resource.assert_called_once_with(agent_id)
            mock_health.assert_called_once_with(agent_id)
    
    @pytest.mark.asyncio
    async def test_start_agent(self, mock_agent):
        """Test starting an agent."""
        runtime = AgentRuntime()
        
        # Register the agent first
        with mock.patch.object(runtime, '_setup_state_persistence'), \
             mock.patch.object(runtime, '_setup_resource_tracking'), \
             mock.patch.object(runtime, '_setup_health_monitoring'):
            
            agent_id = await runtime.register_agent(mock_agent)
        
        # Start the agent
        await runtime.start_agent(agent_id)
        
        # Verify the agent status is updated
        assert runtime._agents[agent_id].status == AgentStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_stop_agent(self, mock_agent):
        """Test stopping an agent."""
        runtime = AgentRuntime()
        
        # Register and start the agent first
        with mock.patch.object(runtime, '_setup_state_persistence'), \
             mock.patch.object(runtime, '_setup_resource_tracking'), \
             mock.patch.object(runtime, '_setup_health_monitoring'):
            
            agent_id = await runtime.register_agent(mock_agent)
            await runtime.start_agent(agent_id)
        
        # Stop the agent
        await runtime.stop_agent(agent_id)
        
        # Verify the agent status is updated
        assert runtime._agents[agent_id].status == AgentStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_run_agent(self, mock_agent):
        """Test running an agent."""
        runtime = AgentRuntime()
        
        # Register and start the agent first
        with mock.patch.object(runtime, '_setup_state_persistence'), \
             mock.patch.object(runtime, '_setup_resource_tracking'), \
             mock.patch.object(runtime, '_setup_health_monitoring'):
            
            agent_id = await runtime.register_agent(mock_agent)
            await runtime.start_agent(agent_id)
        
        # Run the agent
        result = await runtime.run_agent(agent_id, "Test query")
        
        # Verify the agent's run method was called
        mock_agent.run.assert_called_once_with("Test query")
        
        # Verify the result
        assert result == "Test response"
    
    @pytest.mark.asyncio
    async def test_run_agent_not_started(self, mock_agent):
        """Test running an agent that isn't started."""
        runtime = AgentRuntime()
        
        # Register the agent but don't start it
        with mock.patch.object(runtime, '_setup_state_persistence'), \
             mock.patch.object(runtime, '_setup_resource_tracking'), \
             mock.patch.object(runtime, '_setup_health_monitoring'):
            
            agent_id = await runtime.register_agent(mock_agent)
        
        # Attempting to run the agent should raise an exception
        with pytest.raises(AgentRuntimeException):
            await runtime.run_agent(agent_id, "Test query")
    
    @pytest.mark.asyncio
    async def test_get_agent_status(self, mock_agent):
        """Test getting an agent's status."""
        runtime = AgentRuntime()
        
        # Register the agent
        with mock.patch.object(runtime, '_setup_state_persistence'), \
             mock.patch.object(runtime, '_setup_resource_tracking'), \
             mock.patch.object(runtime, '_setup_health_monitoring'):
            
            agent_id = await runtime.register_agent(mock_agent)
        
        # Get the agent's status
        status = runtime.get_agent_status(agent_id)
        
        # Verify the status
        assert status == AgentStatus.REGISTERED
        
        # Update the status
        runtime._agents[agent_id].status = AgentStatus.RUNNING
        
        # Get the updated status
        status = runtime.get_agent_status(agent_id)
        
        # Verify the updated status
        assert status == AgentStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_save_and_restore_state(self, mock_agent):
        """Test saving and restoring agent state."""
        runtime = AgentRuntime()
        
        # Mock the state manager
        mock_state_id = "state-123"
        runtime._state_manager.save_agent_state = mock.AsyncMock(return_value=mock_state_id)
        runtime._state_manager.restore_agent_state = mock.AsyncMock(return_value=mock_agent)
        
        # Register the agent
        with mock.patch.object(runtime, '_setup_state_persistence'), \
             mock.patch.object(runtime, '_setup_resource_tracking'), \
             mock.patch.object(runtime, '_setup_health_monitoring'):
            
            agent_id = await runtime.register_agent(mock_agent)
            await runtime.start_agent(agent_id)
        
        # Save the agent's state
        state_id = await runtime.save_state(agent_id)
        
        # Verify the state manager was called
        runtime._state_manager.save_agent_state.assert_called_once_with(mock_agent)
        assert state_id == mock_state_id
        
        # Restore the state to a new agent
        new_agent_id = await runtime.restore_agent(state_id)
        
        # Verify the state manager was called
        runtime._state_manager.restore_agent_state.assert_called_once_with(state_id)
        
        # Verify the new agent is registered and started
        assert new_agent_id in runtime._agents
        assert runtime._agents[new_agent_id].status == AgentStatus.RUNNING 