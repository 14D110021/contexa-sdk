"""Local agent runtime implementation.

This module provides a local implementation of the Agent Runtime interface
for running and managing agents on the local machine.
"""

import asyncio
import logging
import os
import threading
import time
import uuid
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional, Set, Tuple, cast

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.runtime.agent_runtime import (
    AgentRuntime, 
    AgentRuntimeConfig,
    AgentRuntimeStatus,
)
from contexa_sdk.runtime.health_monitoring import (
    HealthCheck,
    HealthMonitor,
    ResourceHealthCheck,
    ResponseTimeHealthCheck,
)
from contexa_sdk.runtime.resource_tracking import (
    ResourceLimits,
    ResourceTracker,
    ResourceUsage,
)
from contexa_sdk.runtime.state_management import (
    AgentState,
    AgentStateStatus,
    InMemoryStateProvider,
    StateProvider,
)


class LocalAgentRuntime(AgentRuntime):
    """Local implementation of the Agent Runtime interface.
    
    This runtime manages agents running locally in the same process or machine.
    It provides comprehensive agent lifecycle management including:
    
    - Resource tracking and limitation
    - State persistence and recovery
    - Health monitoring and automated recovery
    - Concurrent agent execution
    - Agent pause/resume functionality
    
    The LocalAgentRuntime is designed for development, testing, and production
    deployments where all agents run on a single machine. It automatically
    handles background tasks like health monitoring and state persistence
    while providing a clean API for agent management.
    
    Attributes:
        _config: Configuration settings for the runtime
        _status: Current operational status of the runtime
        _agents: Dictionary mapping agent IDs to agent instances
        _agent_tasks: Dictionary mapping agent IDs to running tasks
        _agent_status: Dictionary mapping agent IDs to agent status values
        _state_provider: Provider for agent state persistence
        _resource_tracker: Tracker for agent resource usage
        _health_monitor: Monitor for agent health status
    """
    
    def __init__(self, config: Optional[AgentRuntimeConfig] = None):
        """Initialize a local agent runtime.
        
        Sets up the runtime with the provided configuration or default settings.
        Initializes supporting components like the state provider, resource tracker,
        and health monitor. The runtime is not started until the start() method
        is called.
        
        Args:
            config: Runtime configuration with settings for max agents, resource limits,
                state persistence, and health monitoring. If None, default configuration
                is used with in-memory state persistence.
                
        Note:
            This constructor only initializes the runtime structures but doesn't
            start background tasks or load agent state. Call start() to fully
            initialize the runtime.
        """
        self._config = config or AgentRuntimeConfig()
        self._status = AgentRuntimeStatus.INITIALIZING
        self._agents: Dict[str, ContexaAgent] = {}
        self._agent_tasks: Dict[str, asyncio.Task] = {}
        self._agent_status: Dict[str, AgentStateStatus] = {}
        
        # Initialize state provider
        self._state_provider = self._config.state_provider or InMemoryStateProvider()
        
        # Initialize resource tracker
        self._resource_tracker = ResourceTracker()
        
        # Initialize health monitor
        self._health_monitor = HealthMonitor(
            check_interval_seconds=self._config.health_check_interval_seconds
        )
        
        # Register default health checks
        self._health_monitor.register_health_check(ResourceHealthCheck())
        self._health_monitor.register_health_check(ResponseTimeHealthCheck())
        
        # Set up logging
        self._logger = logging.getLogger(self.__class__.__name__)
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        # Event loop for async operations
        self._loop = asyncio.get_event_loop()
        
        # Set up background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._state_save_task: Optional[asyncio.Task] = None
        
        # Track if the runtime is initialized
        self._initialized = False
    
    async def start(self) -> None:
        """Start the runtime.
        
        This initializes the runtime and starts background tasks for
        health monitoring and state persistence.
        """
        if self._status != AgentRuntimeStatus.INITIALIZING:
            raise RuntimeError(
                f"Cannot start runtime in state {self._status.name}"
            )
        
        try:
            # Initialize the state provider
            await self._state_provider.initialize()
            
            # Start the health check background task
            self._health_check_task = asyncio.create_task(
                self._health_check_loop()
            )
            
            # Start the state save background task
            self._state_save_task = asyncio.create_task(
                self._state_save_loop()
            )
            
            # Load existing agent states if available
            agent_states = await self._state_provider.list_agent_states()
            for agent_id in agent_states:
                try:
                    # This could be extended to restore agents from state
                    self._logger.info(f"Found saved state for agent {agent_id}")
                except Exception as e:
                    self._logger.error(
                        f"Error loading state for agent {agent_id}: {str(e)}"
                    )
            
            # Mark as initialized
            self._initialized = True
            self._status = AgentRuntimeStatus.RUNNING
            self._logger.info("LocalAgentRuntime started successfully")
            
        except Exception as e:
            self._status = AgentRuntimeStatus.ERROR
            self._logger.error(f"Error starting runtime: {str(e)}")
            raise
    
    async def stop(self) -> None:
        """Stop the runtime.
        
        This stops all running agents and background tasks, and
        persists agent state.
        """
        if self._status == AgentRuntimeStatus.STOPPED:
            return
        
        self._status = AgentRuntimeStatus.STOPPING
        
        try:
            # Cancel health check task
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
                self._health_check_task = None
            
            # Cancel state save task
            if self._state_save_task:
                self._state_save_task.cancel()
                try:
                    await self._state_save_task
                except asyncio.CancelledError:
                    pass
                self._state_save_task = None
            
            # Stop all running agents
            agent_ids = list(self._agents.keys())
            for agent_id in agent_ids:
                try:
                    await self.stop_agent(agent_id)
                except Exception as e:
                    self._logger.error(
                        f"Error stopping agent {agent_id}: {str(e)}"
                    )
            
            # Clean up resources
            self._resource_tracker = ResourceTracker()
            
            self._status = AgentRuntimeStatus.STOPPED
            self._logger.info("LocalAgentRuntime stopped successfully")
            
        except Exception as e:
            self._status = AgentRuntimeStatus.ERROR
            self._logger.error(f"Error stopping runtime: {str(e)}")
            raise
    
    async def pause(self) -> None:
        """Pause the runtime.
        
        This pauses all background tasks but keeps agent state in memory.
        """
        if self._status != AgentRuntimeStatus.RUNNING:
            raise RuntimeError(
                f"Cannot pause runtime in state {self._status.name}"
            )
        
        self._status = AgentRuntimeStatus.PAUSED
        
        # Pause health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
        
        # Pause state save task
        if self._state_save_task:
            self._state_save_task.cancel()
            try:
                await self._state_save_task
            except asyncio.CancelledError:
                pass
            self._state_save_task = None
        
        # Pause all running agents
        agent_ids = list(self._agents.keys())
        for agent_id in agent_ids:
            try:
                await self.pause_agent(agent_id)
            except Exception as e:
                self._logger.error(
                    f"Error pausing agent {agent_id}: {str(e)}"
                )
        
        self._logger.info("LocalAgentRuntime paused successfully")
    
    async def resume(self) -> None:
        """Resume the runtime.
        
        This resumes all background tasks and previously running agents.
        """
        if self._status != AgentRuntimeStatus.PAUSED:
            raise RuntimeError(
                f"Cannot resume runtime in state {self._status.name}"
            )
        
        # Restart background tasks
        self._health_check_task = asyncio.create_task(
            self._health_check_loop()
        )
        self._state_save_task = asyncio.create_task(
            self._state_save_loop()
        )
        
        # Resume all paused agents
        agent_ids = list(self._agents.keys())
        for agent_id in agent_ids:
            try:
                await self.resume_agent(agent_id)
            except Exception as e:
                self._logger.error(
                    f"Error resuming agent {agent_id}: {str(e)}"
                )
        
        self._status = AgentRuntimeStatus.RUNNING
        self._logger.info("LocalAgentRuntime resumed successfully")
    
    async def register_agent(
        self, 
        agent: ContexaAgent, 
        agent_id: Optional[str] = None, 
        resource_limits: Optional[ResourceLimits] = None
    ) -> str:
        """Register an agent with the runtime.
        
        Args:
            agent: The agent to register
            agent_id: Optional ID for the agent. If not provided, a UUID is generated.
            resource_limits: Optional resource limits for the agent.
                If not provided, the default limits from the runtime config are used.
        
        Returns:
            The agent ID
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        # Generate an ID if not provided
        if agent_id is None:
            agent_id = str(uuid.uuid4())
        
        # Check if agent already registered
        with self._lock:
            if agent_id in self._agents:
                raise ValueError(f"Agent with ID {agent_id} already registered")
            
            # Store the agent
            self._agents[agent_id] = agent
            self._agent_status[agent_id] = AgentStateStatus.INITIALIZING
            
            # Register with resource tracker
            limits = resource_limits or self._config.default_resource_limits
            self._resource_tracker.register_agent(agent_id, limits)
            
            self._logger.info(f"Agent {agent_id} registered")
            
            return agent_id
    
    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the runtime.
        
        Args:
            agent_id: ID of the agent to unregister
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        with self._lock:
            if agent_id not in self._agents:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            # Check if agent is running and stop it
            if agent_id in self._agent_tasks:
                try:
                    await self.stop_agent(agent_id)
                except Exception as e:
                    self._logger.error(
                        f"Error stopping agent {agent_id}: {str(e)}"
                    )
            
            # Unregister from resource tracker
            self._resource_tracker.unregister_agent(agent_id)
            
            # Remove agent
            del self._agents[agent_id]
            del self._agent_status[agent_id]
            
            # Clean up health data
            self._health_monitor.clear_health_data(agent_id)
            
            self._logger.info(f"Agent {agent_id} unregistered")
    
    async def get_agent_status(self, agent_id: str) -> AgentStateStatus:
        """Get the status of an agent.
        
        Args:
            agent_id: ID of the agent to check
        
        Returns:
            The current status of the agent
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        with self._lock:
            if agent_id not in self._agents:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            return self._agent_status[agent_id]
    
    async def run_agent(
        self, 
        agent_id: str, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Run an agent with a query and return its response.
        
        Executes the specified agent with the given query and optional context.
        This method handles resource tracking, status updates, response time
        measurement, and token usage estimation. It's the primary method for
        interacting with agents managed by this runtime.
        
        The method performs the following steps:
        1. Validates runtime and agent state
        2. Updates agent status to RUNNING
        3. Tracks request start time and resource usage
        4. Executes the agent with the query
        5. Records response time and estimated token usage
        6. Updates agent status to READY
        7. Returns the agent's response
        
        Args:
            agent_id: Unique identifier of the agent to run. Must be a registered agent.
            query: The text query or instruction to send to the agent.
            context: Optional dictionary containing additional context information
                for the agent. This can include conversation history, user information,
                or any other data needed by the agent. Defaults to an empty dict.
        
        Returns:
            The text response from the agent.
        
        Raises:
            RuntimeError: If the runtime is not initialized or not in RUNNING state.
            ValueError: If the agent with the given ID is not registered.
            Exception: Any exception raised by the agent during execution is
                propagated after logging and status updates.
        
        Note:
            This method automatically tracks resource usage and response times,
            which are used by health monitoring to detect issues with agents.
            Token usage is currently estimated based on response length, but
            more accurate tracking could be implemented in ContexaAgent.
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        if self._status != AgentRuntimeStatus.RUNNING:
            raise RuntimeError(
                f"Cannot run agent in runtime state {self._status.name}"
            )
        
        with self._lock:
            if agent_id not in self._agents:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            agent = self._agents[agent_id]
            
            # Update agent status
            self._agent_status[agent_id] = AgentStateStatus.RUNNING
        
        # Record the start time for response time tracking
        start_time = time.time()
        
        # Track resource usage for this request
        self._resource_tracker.record_request(agent_id)
        
        try:
            # Run the agent
            response = await agent.run(query, context=context or {})
            
            # Record resource usage
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # Record response time for health check
            for health_check in self._health_monitor._health_checks.values():
                if isinstance(health_check, ResponseTimeHealthCheck):
                    health_check.record_response_time(agent_id, response_time_ms)
            
            # Record token usage if available in response metadata
            # This would require adding token usage tracking to ContexaAgent
            # For now, we'll just estimate based on response length
            estimated_tokens = len(response) / 4  # Rough estimate
            self._resource_tracker.record_tokens(agent_id, estimated_tokens)
            
            # Update agent status
            with self._lock:
                self._agent_status[agent_id] = AgentStateStatus.READY
            
            # Record request completion
            self._resource_tracker.complete_request(agent_id)
            
            return response
            
        except Exception as e:
            self._logger.error(f"Error running agent {agent_id}: {str(e)}")
            
            # Update agent status
            with self._lock:
                self._agent_status[agent_id] = AgentStateStatus.ERROR
            
            # Record request completion (even though it failed)
            self._resource_tracker.complete_request(agent_id)
            
            raise
    
    async def save_agent_state(self, agent_id: str) -> None:
        """Save the current state of an agent.
        
        Args:
            agent_id: ID of the agent to save
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        with self._lock:
            if agent_id not in self._agents:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            agent = self._agents[agent_id]
            status = self._agent_status[agent_id]
        
        # Create agent state object
        agent_state = AgentState(
            agent_id=agent_id,
            agent_type=agent.__class__.__name__,
            status=status,
            timestamp=time.time(),
            conversation_history=agent.memory.to_dict() if agent.memory else {},
            config=agent.config.to_dict() if hasattr(agent, 'config') else {},
            metadata={
                'name': agent.name,
                'description': agent.description,
            },
            custom_data={},
        )
        
        # Save the state
        await self._state_provider.save_agent_state(agent_state)
        self._logger.info(f"Saved state for agent {agent_id}")
    
    async def load_agent_state(self, agent_id: str) -> None:
        """Load saved state for an agent.
        
        Args:
            agent_id: ID of the agent to load state for
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        with self._lock:
            if agent_id not in self._agents:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            agent = self._agents[agent_id]
        
        # Load the agent state
        agent_state = await self._state_provider.load_agent_state(agent_id)
        if not agent_state:
            self._logger.warning(f"No saved state found for agent {agent_id}")
            return
        
        # Update agent memory if available
        if agent.memory and agent_state.conversation_history:
            try:
                agent.memory.from_dict(agent_state.conversation_history)
                self._logger.info(f"Loaded conversation history for agent {agent_id}")
            except Exception as e:
                self._logger.error(
                    f"Error loading conversation history for agent {agent_id}: {str(e)}"
                )
        
        # Update agent status
        with self._lock:
            self._agent_status[agent_id] = agent_state.status
        
        self._logger.info(f"Loaded state for agent {agent_id}")
    
    async def get_resource_usage(self, agent_id: str) -> ResourceUsage:
        """Get resource usage information for an agent.
        
        Args:
            agent_id: ID of the agent to check
        
        Returns:
            Current resource usage for the agent
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        with self._lock:
            if agent_id not in self._agents:
                raise ValueError(f"Agent with ID {agent_id} not registered")
        
        # Get resource usage from tracker
        return self._resource_tracker.get_usage(agent_id)
    
    async def check_health(self, agent_id: str) -> Dict[str, Any]:
        """Check the health of an agent.
        
        Args:
            agent_id: ID of the agent to check
        
        Returns:
            Health check results for the agent
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        with self._lock:
            if agent_id not in self._agents:
                raise ValueError(f"Agent with ID {agent_id} not registered")
        
        # Get agent resource usage
        usage = await self.get_resource_usage(agent_id)
        
        # Get agent resource limits
        limits = self._resource_tracker.get_limits(agent_id)
        
        # Context for health checks
        context = {
            'agent_id': agent_id,
            'usage': usage,
            'limits': limits,
        }
        
        # Run health checks
        results = await self._health_monitor.check_health(agent_id, context)
        
        # Get overall health details
        return self._health_monitor.get_health_details(agent_id)
    
    async def recover_agent(self, agent_id: str) -> bool:
        """Recover an agent from a failed state.
        
        Args:
            agent_id: ID of the agent to recover
        
        Returns:
            True if recovery was successful, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        with self._lock:
            if agent_id not in self._agents:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            if self._agent_status[agent_id] != AgentStateStatus.ERROR:
                self._logger.info(
                    f"Agent {agent_id} is not in error state, no recovery needed"
                )
                return True
        
        try:
            # Load saved state if available
            await self.load_agent_state(agent_id)
            
            # Reset agent status
            with self._lock:
                self._agent_status[agent_id] = AgentStateStatus.READY
            
            self._logger.info(f"Agent {agent_id} recovered successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Error recovering agent {agent_id}: {str(e)}")
            return False
    
    async def _health_check_loop(self) -> None:
        """Background task for running periodic health checks."""
        try:
            while True:
                if self._status == AgentRuntimeStatus.RUNNING:
                    # Check health for all agents
                    with self._lock:
                        agent_ids = list(self._agents.keys())
                    
                    for agent_id in agent_ids:
                        try:
                            health_details = await self.check_health(agent_id)
                            if health_details["status"] in ("CRITICAL", "UNHEALTHY"):
                                self._logger.warning(
                                    f"Agent {agent_id} health status: {health_details['status']}"
                                )
                                
                                # Attempt auto-recovery for unhealthy agents
                                with self._lock:
                                    if (agent_id in self._agent_status and 
                                            self._agent_status[agent_id] == AgentStateStatus.ERROR):
                                        self._logger.info(f"Attempting auto-recovery for agent {agent_id}")
                                        await self.recover_agent(agent_id)
                                        
                        except Exception as e:
                            self._logger.error(
                                f"Error checking health for agent {agent_id}: {str(e)}"
                            )
                
                # Sleep for the configured interval
                await asyncio.sleep(self._config.health_check_interval_seconds)
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            pass
        except Exception as e:
            self._logger.error(f"Error in health check loop: {str(e)}")
    
    async def _state_save_loop(self) -> None:
        """Background task for periodically saving agent state."""
        try:
            # State save interval (default to 5 minutes)
            save_interval = self._config.additional_options.get(
                "state_save_interval_seconds", 300
            )
            
            while True:
                if self._status == AgentRuntimeStatus.RUNNING:
                    # Save state for all agents
                    with self._lock:
                        agent_ids = list(self._agents.keys())
                    
                    for agent_id in agent_ids:
                        try:
                            await self.save_agent_state(agent_id)
                        except Exception as e:
                            self._logger.error(
                                f"Error saving state for agent {agent_id}: {str(e)}"
                            )
                
                # Sleep for the configured interval
                await asyncio.sleep(save_interval)
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            # Save state for all agents before exiting
            with self._lock:
                agent_ids = list(self._agents.keys())
            
            for agent_id in agent_ids:
                try:
                    await self.save_agent_state(agent_id)
                except Exception as e:
                    self._logger.error(
                        f"Error saving state for agent {agent_id}: {str(e)}"
                    )
        except Exception as e:
            self._logger.error(f"Error in state save loop: {str(e)}")
            
    # Additional methods for managing individual agents
    
    async def start_agent(self, agent_id: str) -> None:
        """Start a specific agent.
        
        Args:
            agent_id: ID of the agent to start
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        with self._lock:
            if agent_id not in self._agents:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            if self._agent_status[agent_id] == AgentStateStatus.RUNNING:
                self._logger.info(f"Agent {agent_id} is already running")
                return
            
            # Update agent status
            self._agent_status[agent_id] = AgentStateStatus.READY
            
            self._logger.info(f"Agent {agent_id} started")
    
    async def stop_agent(self, agent_id: str) -> None:
        """Stop a specific agent.
        
        Args:
            agent_id: ID of the agent to stop
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        with self._lock:
            if agent_id not in self._agents:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            # Cancel any running task
            if agent_id in self._agent_tasks:
                task = self._agent_tasks[agent_id]
                task.cancel()
                del self._agent_tasks[agent_id]
            
            # Update agent status
            self._agent_status[agent_id] = AgentStateStatus.COMPLETED
            
            # Save agent state before stopping
            try:
                await self.save_agent_state(agent_id)
            except Exception as e:
                self._logger.error(
                    f"Error saving state for agent {agent_id}: {str(e)}"
                )
            
            self._logger.info(f"Agent {agent_id} stopped")
    
    async def pause_agent(self, agent_id: str) -> None:
        """Pause a specific agent.
        
        Args:
            agent_id: ID of the agent to pause
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        with self._lock:
            if agent_id not in self._agents:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            # Can't truly pause a running agent, but we can update its status
            if self._agent_status[agent_id] == AgentStateStatus.RUNNING:
                self._logger.warning(
                    f"Agent {agent_id} is currently running and cannot be truly paused"
                )
            
            # Update agent status
            self._agent_status[agent_id] = AgentStateStatus.PAUSED
            
            # Save agent state
            try:
                await self.save_agent_state(agent_id)
            except Exception as e:
                self._logger.error(
                    f"Error saving state for agent {agent_id}: {str(e)}"
                )
            
            self._logger.info(f"Agent {agent_id} paused")
    
    async def resume_agent(self, agent_id: str) -> None:
        """Resume a paused agent.
        
        Args:
            agent_id: ID of the agent to resume
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        with self._lock:
            if agent_id not in self._agents:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            if self._agent_status[agent_id] != AgentStateStatus.PAUSED:
                self._logger.warning(
                    f"Agent {agent_id} is not paused, cannot resume"
                )
                return
            
            # Update agent status
            self._agent_status[agent_id] = AgentStateStatus.READY
            
            self._logger.info(f"Agent {agent_id} resumed") 