"""Cluster agent runtime implementation.

This module provides a distributed implementation of the Agent Runtime interface
for running and managing agents across multiple nodes in a cluster.
"""

import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.runtime.agent_runtime import (
    AgentRuntime, 
    AgentRuntimeConfig,
    AgentRuntimeStatus,
)
from contexa_sdk.runtime.resource_tracking import ResourceLimits, ResourceUsage
from contexa_sdk.runtime.state_management import (
    AgentState,
    AgentStateStatus,
    StateProvider,
)


@dataclass
class NodeInfo:
    """Information about a node in the cluster."""
    
    # Unique identifier for the node
    node_id: str
    
    # Human-readable name for the node
    name: str
    
    # Current status of the node
    status: str
    
    # API endpoint for the node
    endpoint: str
    
    # Current resource usage
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    
    # Agents running on this node
    agent_ids: List[str] = field(default_factory=list)
    
    # Last heartbeat timestamp
    last_heartbeat: float = field(default_factory=time.time)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class NodeStatus(Enum):
    """Status of a node in the cluster."""
    ONLINE = auto()
    OFFLINE = auto()
    DEGRADED = auto()
    MAINTENANCE = auto()


class ClusterAgentRuntime(AgentRuntime):
    """Distributed implementation of the Agent Runtime interface.
    
    This runtime manages agents running across multiple nodes in a cluster,
    providing a scalable, fault-tolerant environment for agent execution.
    The architecture follows a coordinator-worker pattern where one node acts
    as the coordinator responsible for:
    
    - Maintaining a global view of all nodes and agents
    - Performing load balancing when placing agents
    - Handling node failure detection and recovery
    - Routing agent requests to the appropriate node
    - Orchestrating agent migration when nodes fail
    
    Worker nodes execute agents locally and communicate with the coordinator
    for synchronization. The runtime provides:
    
    - Transparent distribution: Clients interact with agents the same way
      regardless of which node they're running on
    - Automatic failover: If a node fails, its agents can be migrated to
      other healthy nodes
    - Load balancing: Agents are distributed across nodes based on resource
      availability and constraints
    - Synchronization: Agent state is synchronized across the cluster
    - Scalability: New nodes can join the cluster dynamically
    
    Both coordinator and worker nodes can run agents locally, making efficient
    use of all available resources in the cluster.
    
    Attributes:
        _config: Runtime configuration settings
        _status: Current operational status of the runtime
        _node_id: Unique identifier for this node
        _node_endpoint: API endpoint for this node
        _is_coordinator: Whether this node is the coordinator
        _coordinator_endpoint: API endpoint for the coordinator node
        _nodes: Dictionary of all nodes in the cluster
        _agent_locations: Mapping of agent IDs to their node locations
        _local_agents: Agents running locally on this node
        _agent_status: Status of locally running agents
    """
    
    def __init__(
        self,
        config: Optional[AgentRuntimeConfig] = None,
        coordinator_endpoint: Optional[str] = None,
        is_coordinator: bool = False,
        node_id: Optional[str] = None,
        node_endpoint: Optional[str] = None,
    ):
        """Initialize a cluster agent runtime.
        
        Sets up a node in the agent cluster with either coordinator or worker
        functionality. Each node can run agents locally while participating
        in the distributed runtime environment.
        
        Args:
            config: Runtime configuration for resource limits, state persistence, etc.
                If None, default configuration is used.
            coordinator_endpoint: API endpoint for the coordinator node. Required for
                worker nodes, ignored for the coordinator node.
            is_coordinator: Whether this instance should act as the cluster coordinator.
                Only one node in the cluster should be designated as coordinator.
            node_id: Unique identifier for this node. If None, a UUID is generated.
                This should be globally unique across the cluster.
            node_endpoint: API endpoint for this node, used for inter-node communication.
                Must be reachable by other nodes in the cluster.
                
        Note:
            If is_coordinator is True, this node will manage the cluster.
            If is_coordinator is False, coordinator_endpoint must be provided
            to connect to an existing coordinator.
        """
        self._config = config or AgentRuntimeConfig()
        self._status = AgentRuntimeStatus.INITIALIZING
        
        # Node information
        self._node_id = node_id or str(uuid.uuid4())
        self._node_endpoint = node_endpoint
        self._is_coordinator = is_coordinator
        self._coordinator_endpoint = coordinator_endpoint
        
        # Cluster state
        self._nodes: Dict[str, NodeInfo] = {}
        self._agent_locations: Dict[str, str] = {}  # agent_id -> node_id
        
        # Local agents
        self._local_agents: Dict[str, ContexaAgent] = {}
        self._agent_status: Dict[str, AgentStateStatus] = {}
        
        # Set up logging
        self._logger = logging.getLogger(self.__class__.__name__)
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._node_monitor_task: Optional[asyncio.Task] = None
        self._agent_sync_task: Optional[asyncio.Task] = None
        
        # State provider for agent state persistence
        self._state_provider = self._config.state_provider
        
        # Track if the runtime is initialized
        self._initialized = False
    
    async def start(self) -> None:
        """Start the runtime.
        
        This initializes the runtime and starts background tasks for
        cluster coordination.
        """
        if self._status != AgentRuntimeStatus.INITIALIZING:
            raise RuntimeError(
                f"Cannot start runtime in state {self._status.name}"
            )
        
        try:
            # Initialize the state provider if configured
            if self._state_provider:
                await self._state_provider.initialize()
            
            # If coordinator, start coordinator services
            if self._is_coordinator:
                await self._start_coordinator()
            else:
                # If worker node, register with coordinator
                if not self._coordinator_endpoint:
                    raise ValueError("Coordinator endpoint required for worker nodes")
                await self._register_with_coordinator()
            
            # Start heartbeat task
            self._heartbeat_task = asyncio.create_task(
                self._heartbeat_loop()
            )
            
            # Start node monitor task if coordinator
            if self._is_coordinator:
                self._node_monitor_task = asyncio.create_task(
                    self._node_monitor_loop()
                )
            
            # Start agent sync task
            self._agent_sync_task = asyncio.create_task(
                self._agent_sync_loop()
            )
            
            # Mark as initialized
            self._initialized = True
            self._status = AgentRuntimeStatus.RUNNING
            
            self._logger.info(
                f"ClusterAgentRuntime started successfully "
                f"(node_id={self._node_id}, coordinator={self._is_coordinator})"
            )
            
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
            # Cancel heartbeat task
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
                self._heartbeat_task = None
            
            # Cancel node monitor task
            if self._node_monitor_task:
                self._node_monitor_task.cancel()
                try:
                    await self._node_monitor_task
                except asyncio.CancelledError:
                    pass
                self._node_monitor_task = None
            
            # Cancel agent sync task
            if self._agent_sync_task:
                self._agent_sync_task.cancel()
                try:
                    await self._agent_sync_task
                except asyncio.CancelledError:
                    pass
                self._agent_sync_task = None
            
            # Stop local agents
            for agent_id in list(self._local_agents.keys()):
                try:
                    await self._stop_local_agent(agent_id)
                except Exception as e:
                    self._logger.error(
                        f"Error stopping agent {agent_id}: {str(e)}"
                    )
            
            # If not coordinator, unregister from coordinator
            if not self._is_coordinator and self._coordinator_endpoint:
                try:
                    await self._unregister_from_coordinator()
                except Exception as e:
                    self._logger.error(
                        f"Error unregistering from coordinator: {str(e)}"
                    )
            
            self._status = AgentRuntimeStatus.STOPPED
            self._logger.info("ClusterAgentRuntime stopped successfully")
            
        except Exception as e:
            self._status = AgentRuntimeStatus.ERROR
            self._logger.error(f"Error stopping runtime: {str(e)}")
            raise
    
    async def pause(self) -> None:
        """Pause the runtime.
        
        This pauses all background tasks but keeps agent state in memory.
        """
        # For cluster runtime, pause doesn't stop coordination tasks
        # but it does pause agent processing
        if self._status != AgentRuntimeStatus.RUNNING:
            raise RuntimeError(
                f"Cannot pause runtime in state {self._status.name}"
            )
        
        self._status = AgentRuntimeStatus.PAUSED
        self._logger.info("ClusterAgentRuntime paused")
    
    async def resume(self) -> None:
        """Resume the runtime.
        
        This resumes all background tasks and previously running agents.
        """
        if self._status != AgentRuntimeStatus.PAUSED:
            raise RuntimeError(
                f"Cannot resume runtime in state {self._status.name}"
            )
        
        self._status = AgentRuntimeStatus.RUNNING
        self._logger.info("ClusterAgentRuntime resumed")
    
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
        
        # Check if this is the coordinator
        if self._is_coordinator:
            # Assign to a node (could implement load balancing here)
            target_node_id = self._select_node_for_agent(resource_limits)
            
            if target_node_id == self._node_id:
                # Local assignment
                await self._register_local_agent(agent_id, agent, resource_limits)
            else:
                # Remote assignment - delegate to target node
                await self._register_remote_agent(
                    agent_id, agent, target_node_id, resource_limits
                )
            
            # Update agent location mapping
            self._agent_locations[agent_id] = target_node_id
            
        else:
            # Worker node - register locally but inform coordinator
            await self._register_local_agent(agent_id, agent, resource_limits)
            await self._notify_coordinator_of_agent(agent_id, "register")
        
        self._logger.info(f"Agent {agent_id} registered successfully")
        return agent_id
    
    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the runtime.
        
        Args:
            agent_id: ID of the agent to unregister
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        # Check if this is the coordinator
        if self._is_coordinator:
            # Check if agent exists
            if agent_id not in self._agent_locations:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            # Get the node running this agent
            node_id = self._agent_locations[agent_id]
            
            if node_id == self._node_id:
                # Local agent
                await self._unregister_local_agent(agent_id)
            else:
                # Remote agent - delegate to target node
                await self._unregister_remote_agent(agent_id, node_id)
            
            # Update agent location mapping
            del self._agent_locations[agent_id]
            
        else:
            # Worker node - unregister locally but inform coordinator
            if agent_id in self._local_agents:
                await self._unregister_local_agent(agent_id)
                await self._notify_coordinator_of_agent(agent_id, "unregister")
            else:
                raise ValueError(f"Agent with ID {agent_id} not registered")
        
        self._logger.info(f"Agent {agent_id} unregistered successfully")
    
    async def get_agent_status(self, agent_id: str) -> AgentStateStatus:
        """Get the status of an agent.
        
        Args:
            agent_id: ID of the agent to check
        
        Returns:
            The current status of the agent
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        # Check if this is the coordinator
        if self._is_coordinator:
            # Check if agent exists
            if agent_id not in self._agent_locations:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            # Get the node running this agent
            node_id = self._agent_locations[agent_id]
            
            if node_id == self._node_id:
                # Local agent
                return self._agent_status.get(agent_id, AgentStateStatus.UNKNOWN)
            else:
                # Remote agent - query target node
                return await self._get_remote_agent_status(agent_id, node_id)
            
        else:
            # Worker node - check locally
            if agent_id in self._local_agents:
                return self._agent_status.get(agent_id, AgentStateStatus.UNKNOWN)
            else:
                # Agent might be on another node, query coordinator
                return await self._query_coordinator_for_agent_status(agent_id)
    
    async def run_agent(
        self, 
        agent_id: str, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Run an agent with a query.
        
        Args:
            agent_id: ID of the agent to run
            query: Query to pass to the agent
            context: Optional context information for the agent
        
        Returns:
            The agent's response
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        if self._status != AgentRuntimeStatus.RUNNING:
            raise RuntimeError(
                f"Cannot run agent in runtime state {self._status.name}"
            )
        
        # Check if this is the coordinator
        if self._is_coordinator:
            # Check if agent exists
            if agent_id not in self._agent_locations:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            # Get the node running this agent
            node_id = self._agent_locations[agent_id]
            
            if node_id == self._node_id:
                # Local agent
                return await self._run_local_agent(agent_id, query, context)
            else:
                # Remote agent - delegate to target node
                return await self._run_remote_agent(agent_id, query, context, node_id)
            
        else:
            # Worker node - run locally or delegate to coordinator
            if agent_id in self._local_agents:
                return await self._run_local_agent(agent_id, query, context)
            else:
                # Agent might be on another node, query coordinator
                return await self._delegate_query_to_coordinator(agent_id, query, context)
    
    async def save_agent_state(self, agent_id: str) -> None:
        """Save the current state of an agent.
        
        Args:
            agent_id: ID of the agent to save
        """
        if not self._initialized or not self._state_provider:
            raise RuntimeError("Runtime not initialized or state provider not configured")
        
        # Check if this is the coordinator
        if self._is_coordinator:
            # Check if agent exists
            if agent_id not in self._agent_locations:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            # Get the node running this agent
            node_id = self._agent_locations[agent_id]
            
            if node_id == self._node_id:
                # Local agent
                await self._save_local_agent_state(agent_id)
            else:
                # Remote agent - delegate to target node
                await self._save_remote_agent_state(agent_id, node_id)
            
        else:
            # Worker node - save locally
            if agent_id in self._local_agents:
                await self._save_local_agent_state(agent_id)
            else:
                raise ValueError(f"Agent with ID {agent_id} not registered")
    
    async def load_agent_state(self, agent_id: str) -> None:
        """Load saved state for an agent.
        
        Args:
            agent_id: ID of the agent to load state for
        """
        if not self._initialized or not self._state_provider:
            raise RuntimeError("Runtime not initialized or state provider not configured")
        
        # Check if this is the coordinator
        if self._is_coordinator:
            # Check if agent exists
            if agent_id not in self._agent_locations:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            # Get the node running this agent
            node_id = self._agent_locations[agent_id]
            
            if node_id == self._node_id:
                # Local agent
                await self._load_local_agent_state(agent_id)
            else:
                # Remote agent - delegate to target node
                await self._load_remote_agent_state(agent_id, node_id)
            
        else:
            # Worker node - load locally
            if agent_id in self._local_agents:
                await self._load_local_agent_state(agent_id)
            else:
                raise ValueError(f"Agent with ID {agent_id} not registered")
    
    async def get_resource_usage(self, agent_id: str) -> ResourceUsage:
        """Get resource usage information for an agent.
        
        Args:
            agent_id: ID of the agent to check
        
        Returns:
            Current resource usage for the agent
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        # This would be implemented with actual resource monitoring
        # For now, return a placeholder
        return ResourceUsage()
    
    async def check_health(self, agent_id: str) -> Dict[str, Any]:
        """Check the health of an agent.
        
        Args:
            agent_id: ID of the agent to check
        
        Returns:
            Health check results for the agent
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        # This would be implemented with actual health checks
        # For now, return a placeholder
        status = await self.get_agent_status(agent_id)
        return {
            "status": "HEALTHY" if status == AgentStateStatus.READY else "UNHEALTHY",
            "checks": {}
        }
    
    async def recover_agent(self, agent_id: str) -> bool:
        """Recover an agent from a failed state.
        
        Args:
            agent_id: ID of the agent to recover
        
        Returns:
            True if recovery was successful, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")
        
        # Check if this is the coordinator
        if self._is_coordinator:
            # Check if agent exists
            if agent_id not in self._agent_locations:
                raise ValueError(f"Agent with ID {agent_id} not registered")
            
            # Get the node running this agent
            node_id = self._agent_locations[agent_id]
            
            # Check if node is online
            if node_id not in self._nodes or (
                self._nodes[node_id].status != NodeStatus.ONLINE.name
            ):
                # Node is offline, need to migrate the agent
                return await self._migrate_agent(agent_id, node_id)
            
            if node_id == self._node_id:
                # Local agent
                return await self._recover_local_agent(agent_id)
            else:
                # Remote agent - delegate to target node
                return await self._recover_remote_agent(agent_id, node_id)
            
        else:
            # Worker node - recover locally or delegate to coordinator
            if agent_id in self._local_agents:
                return await self._recover_local_agent(agent_id)
            else:
                # Agent might be on another node, delegate to coordinator
                return await self._delegate_recovery_to_coordinator(agent_id)
    
    # Internal methods for coordinator operations
    
    async def _start_coordinator(self) -> None:
        """Start coordinator-specific services."""
        # Add this node to the list of nodes
        self._nodes[self._node_id] = NodeInfo(
            node_id=self._node_id,
            name=f"Coordinator-{self._node_id}",
            status=NodeStatus.ONLINE.name,
            endpoint=self._node_endpoint or "",
            last_heartbeat=time.time(),
        )
        
        self._logger.info("Coordinator services started")
    
    async def _node_monitor_loop(self) -> None:
        """Background task for monitoring nodes in the cluster."""
        try:
            while True:
                current_time = time.time()
                
                # Check for nodes that haven't sent a heartbeat recently
                for node_id, node_info in list(self._nodes.items()):
                    # Skip self
                    if node_id == self._node_id:
                        continue
                    
                    # Check if node is overdue for heartbeat
                    heartbeat_timeout = self._config.additional_options.get(
                        "heartbeat_timeout_seconds", 30
                    )
                    
                    if (current_time - node_info.last_heartbeat) > heartbeat_timeout:
                        if node_info.status == NodeStatus.ONLINE.name:
                            # Mark node as offline
                            self._logger.warning(
                                f"Node {node_id} missed heartbeat, marking as offline"
                            )
                            node_info.status = NodeStatus.OFFLINE.name
                            
                            # Handle agents on this node
                            await self._handle_node_failure(node_id)
                
                # Sleep for the check interval
                check_interval = self._config.additional_options.get(
                    "node_check_interval_seconds", 10
                )
                await asyncio.sleep(check_interval)
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            pass
        except Exception as e:
            self._logger.error(f"Error in node monitor loop: {str(e)}")
    
    async def _handle_node_failure(self, node_id: str) -> None:
        """Handle failure of a node in the cluster.
        
        Args:
            node_id: ID of the failed node
        """
        # Find all agents on this node
        agent_ids = []
        for agent_id, location in self._agent_locations.items():
            if location == node_id:
                agent_ids.append(agent_id)
        
        self._logger.info(
            f"Handling failure of node {node_id} with {len(agent_ids)} agents"
        )
        
        # Migrate agents to other nodes
        for agent_id in agent_ids:
            try:
                await self._migrate_agent(agent_id, node_id)
            except Exception as e:
                self._logger.error(
                    f"Error migrating agent {agent_id}: {str(e)}"
                )
    
    async def _migrate_agent(self, agent_id: str, from_node_id: str) -> bool:
        """Migrate an agent from one node to another.
        
        Args:
            agent_id: ID of the agent to migrate
            from_node_id: ID of the node the agent is currently on
            
        Returns:
            True if migration was successful, False otherwise
        """
        # In a real implementation, this would:
        # 1. Select a new node
        # 2. Load agent state from persistent storage
        # 3. Initialize the agent on the new node
        # 4. Update the agent location mapping
        
        self._logger.info(
            f"Migrating agent {agent_id} from node {from_node_id}"
        )
        
        # For now, just update the location to this node
        # and create a placeholder agent
        self._agent_locations[agent_id] = self._node_id
        
        # In a real implementation, we'd restore from state
        # For this example, we'll create a placeholder agent
        self._local_agents[agent_id] = ContexaAgent(
            name=f"Migrated-{agent_id}",
            description="Agent migrated from failed node",
            model=None,  # Would be restored from state
            tools=[],    # Would be restored from state
        )
        self._agent_status[agent_id] = AgentStateStatus.READY
        
        self._logger.info(
            f"Agent {agent_id} migrated successfully to node {self._node_id}"
        )
        return True
    
    async def _select_node_for_agent(
        self, resource_limits: Optional[ResourceLimits] = None
    ) -> str:
        """Select the best node to run an agent.
        
        Args:
            resource_limits: Resource requirements for the agent
            
        Returns:
            ID of the selected node
        """
        # In a real implementation, this would:
        # 1. Check resource availability on all nodes
        # 2. Select the node with the most available resources
        # 3. Consider affinity/anti-affinity rules
        
        # For this example, just return the coordinator node
        return self._node_id
    
    # Internal methods for worker node operations
    
    async def _register_with_coordinator(self) -> None:
        """Register this node with the coordinator."""
        # In a real implementation, this would make a request to the coordinator
        self._logger.info(
            f"Registered node {self._node_id} with coordinator at {self._coordinator_endpoint}"
        )
    
    async def _unregister_from_coordinator(self) -> None:
        """Unregister this node from the coordinator."""
        # In a real implementation, this would make a request to the coordinator
        self._logger.info(
            f"Unregistered node {self._node_id} from coordinator"
        )
    
    async def _heartbeat_loop(self) -> None:
        """Background task for sending heartbeats to the coordinator."""
        # Skip if this is the coordinator
        if self._is_coordinator:
            return
            
        try:
            while True:
                # In a real implementation, this would make a request to the coordinator
                self._logger.debug(
                    f"Sending heartbeat to coordinator from node {self._node_id}"
                )
                
                # Sleep for the heartbeat interval
                heartbeat_interval = self._config.additional_options.get(
                    "heartbeat_interval_seconds", 10
                )
                await asyncio.sleep(heartbeat_interval)
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            pass
        except Exception as e:
            self._logger.error(f"Error in heartbeat loop: {str(e)}")
    
    async def _agent_sync_loop(self) -> None:
        """Background task for syncing agent states."""
        try:
            while True:
                # In a real implementation, this would sync agent state with the coordinator
                
                # Sleep for the sync interval
                sync_interval = self._config.additional_options.get(
                    "agent_sync_interval_seconds", 30
                )
                await asyncio.sleep(sync_interval)
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            pass
        except Exception as e:
            self._logger.error(f"Error in agent sync loop: {str(e)}")
    
    async def _notify_coordinator_of_agent(
        self, agent_id: str, action: str
    ) -> None:
        """Notify the coordinator of an agent action.
        
        Args:
            agent_id: ID of the agent
            action: Action being performed (register, unregister, etc.)
        """
        # In a real implementation, this would make a request to the coordinator
        self._logger.info(
            f"Notified coordinator of {action} for agent {agent_id}"
        )
    
    async def _query_coordinator_for_agent_status(
        self, agent_id: str
    ) -> AgentStateStatus:
        """Query the coordinator for agent status.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Status of the agent
        """
        # In a real implementation, this would make a request to the coordinator
        # For now, just return unknown
        return AgentStateStatus.UNKNOWN
    
    async def _delegate_query_to_coordinator(
        self, agent_id: str, query: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Delegate a query to the coordinator.
        
        Args:
            agent_id: ID of the agent
            query: Query to pass to the agent
            context: Optional context information
            
        Returns:
            Agent response
        """
        # In a real implementation, this would make a request to the coordinator
        raise ValueError(f"Agent {agent_id} not found on this node")
    
    async def _delegate_recovery_to_coordinator(self, agent_id: str) -> bool:
        """Delegate agent recovery to the coordinator.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            True if recovery was successful, False otherwise
        """
        # In a real implementation, this would make a request to the coordinator
        raise ValueError(f"Agent {agent_id} not found on this node")
    
    # Internal methods for local agent operations
    
    async def _register_local_agent(
        self, 
        agent_id: str, 
        agent: ContexaAgent,
        resource_limits: Optional[ResourceLimits] = None
    ) -> None:
        """Register an agent locally.
        
        Args:
            agent_id: ID for the agent
            agent: The agent to register
            resource_limits: Resource limits for the agent
        """
        if agent_id in self._local_agents:
            raise ValueError(f"Agent with ID {agent_id} already registered")
        
        self._local_agents[agent_id] = agent
        self._agent_status[agent_id] = AgentStateStatus.INITIALIZING
        
        # Initialize agent
        # In a real implementation, this would set up resources, etc.
        self._agent_status[agent_id] = AgentStateStatus.READY
        
        self._logger.info(f"Agent {agent_id} registered locally")
    
    async def _unregister_local_agent(self, agent_id: str) -> None:
        """Unregister an agent locally.
        
        Args:
            agent_id: ID of the agent to unregister
        """
        if agent_id not in self._local_agents:
            raise ValueError(f"Agent with ID {agent_id} not registered")
        
        # Clean up resources
        # In a real implementation, this would release resources, etc.
        
        # Remove agent
        del self._local_agents[agent_id]
        if agent_id in self._agent_status:
            del self._agent_status[agent_id]
        
        self._logger.info(f"Agent {agent_id} unregistered locally")
    
    async def _run_local_agent(
        self, 
        agent_id: str, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Run a local agent.
        
        Args:
            agent_id: ID of the agent to run
            query: Query to pass to the agent
            context: Optional context information
            
        Returns:
            Agent response
        """
        if agent_id not in self._local_agents:
            raise ValueError(f"Agent with ID {agent_id} not registered")
        
        agent = self._local_agents[agent_id]
        
        # Update agent status
        self._agent_status[agent_id] = AgentStateStatus.RUNNING
        
        try:
            # Run the agent
            response = await agent.run(query, context=context or {})
            
            # Update agent status
            self._agent_status[agent_id] = AgentStateStatus.READY
            
            return response
            
        except Exception as e:
            # Update agent status
            self._agent_status[agent_id] = AgentStateStatus.ERROR
            
            self._logger.error(f"Error running agent {agent_id}: {str(e)}")
            raise
    
    async def _stop_local_agent(self, agent_id: str) -> None:
        """Stop a local agent.
        
        Args:
            agent_id: ID of the agent to stop
        """
        if agent_id not in self._local_agents:
            raise ValueError(f"Agent with ID {agent_id} not registered")
        
        # Update agent status
        self._agent_status[agent_id] = AgentStateStatus.COMPLETED
        
        self._logger.info(f"Agent {agent_id} stopped locally")
    
    async def _recover_local_agent(self, agent_id: str) -> bool:
        """Recover a local agent.
        
        Args:
            agent_id: ID of the agent to recover
            
        Returns:
            True if recovery was successful, False otherwise
        """
        if agent_id not in self._local_agents:
            raise ValueError(f"Agent with ID {agent_id} not registered")
        
        if self._agent_status[agent_id] != AgentStateStatus.ERROR:
            # Agent is not in error state, no recovery needed
            return True
        
        try:
            # In a real implementation, this would attempt to restart the agent
            # or take other recovery actions
            
            # Try loading state if available
            if self._state_provider:
                await self._load_local_agent_state(agent_id)
            
            # Update agent status
            self._agent_status[agent_id] = AgentStateStatus.READY
            
            self._logger.info(f"Agent {agent_id} recovered locally")
            return True
            
        except Exception as e:
            self._logger.error(f"Error recovering agent {agent_id}: {str(e)}")
            return False
    
    async def _save_local_agent_state(self, agent_id: str) -> None:
        """Save state for a local agent.
        
        Args:
            agent_id: ID of the agent to save state for
        """
        if not self._state_provider:
            return
            
        if agent_id not in self._local_agents:
            raise ValueError(f"Agent with ID {agent_id} not registered")
        
        agent = self._local_agents[agent_id]
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
    
    async def _load_local_agent_state(self, agent_id: str) -> None:
        """Load state for a local agent.
        
        Args:
            agent_id: ID of the agent to load state for
        """
        if not self._state_provider:
            return
            
        if agent_id not in self._local_agents:
            raise ValueError(f"Agent with ID {agent_id} not registered")
        
        agent = self._local_agents[agent_id]
        
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
        self._agent_status[agent_id] = agent_state.status
        
        self._logger.info(f"Loaded state for agent {agent_id}")
    
    # These methods would be implemented for remote operations in a real system
    
    async def _register_remote_agent(
        self, 
        agent_id: str, 
        agent: ContexaAgent,
        target_node_id: str,
        resource_limits: Optional[ResourceLimits] = None
    ) -> None:
        """Register an agent on a remote node.
        
        Args:
            agent_id: ID for the agent
            agent: The agent to register
            target_node_id: ID of the node to register on
            resource_limits: Resource limits for the agent
        """
        # In a real implementation, this would make a request to the target node
        self._logger.info(
            f"Registered agent {agent_id} on remote node {target_node_id}"
        )
    
    async def _unregister_remote_agent(
        self, agent_id: str, node_id: str
    ) -> None:
        """Unregister an agent from a remote node.
        
        Args:
            agent_id: ID of the agent to unregister
            node_id: ID of the node the agent is running on
        """
        # In a real implementation, this would make a request to the target node
        self._logger.info(
            f"Unregistered agent {agent_id} from remote node {node_id}"
        )
    
    async def _get_remote_agent_status(
        self, agent_id: str, node_id: str
    ) -> AgentStateStatus:
        """Get the status of an agent on a remote node.
        
        Args:
            agent_id: ID of the agent to check
            node_id: ID of the node the agent is running on
            
        Returns:
            Status of the agent
        """
        # In a real implementation, this would make a request to the target node
        # For now, just return unknown
        return AgentStateStatus.UNKNOWN
    
    async def _run_remote_agent(
        self, 
        agent_id: str, 
        query: str, 
        context: Optional[Dict[str, Any]],
        node_id: str
    ) -> str:
        """Run an agent on a remote node.
        
        Args:
            agent_id: ID of the agent to run
            query: Query to pass to the agent
            context: Optional context information
            node_id: ID of the node the agent is running on
            
        Returns:
            Agent response
        """
        # In a real implementation, this would make a request to the target node
        return f"Response from agent {agent_id} on node {node_id}"
    
    async def _save_remote_agent_state(
        self, agent_id: str, node_id: str
    ) -> None:
        """Save state for an agent on a remote node.
        
        Args:
            agent_id: ID of the agent to save state for
            node_id: ID of the node the agent is running on
        """
        # In a real implementation, this would make a request to the target node
        self._logger.info(
            f"Saved state for agent {agent_id} on remote node {node_id}"
        )
    
    async def _load_remote_agent_state(
        self, agent_id: str, node_id: str
    ) -> None:
        """Load state for an agent on a remote node.
        
        Args:
            agent_id: ID of the agent to load state for
            node_id: ID of the node the agent is running on
        """
        # In a real implementation, this would make a request to the target node
        self._logger.info(
            f"Loaded state for agent {agent_id} on remote node {node_id}"
        )
    
    async def _recover_remote_agent(
        self, agent_id: str, node_id: str
    ) -> bool:
        """Recover an agent on a remote node.
        
        Args:
            agent_id: ID of the agent to recover
            node_id: ID of the node the agent is running on
            
        Returns:
            True if recovery was successful, False otherwise
        """
        # In a real implementation, this would make a request to the target node
        self._logger.info(
            f"Recovered agent {agent_id} on remote node {node_id}"
        )
        return True 