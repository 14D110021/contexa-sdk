"""State management for agent runtimes.

This module provides interfaces and implementations for persisting and
recovering agent state, allowing for checkpoint/restore capabilities
and recovery from failures.
"""

import abc
import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Union


class AgentStateStatus(Enum):
    """Status of an agent's state."""
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    ERROR = auto()


@dataclass
class AgentState:
    """State information for an agent.
    
    This class represents the serializable state of an agent that can be
    persisted and restored.
    """
    # Unique identifier for the agent
    agent_id: str
    
    # Type of the agent
    agent_type: str
    
    # Current status of the agent
    status: AgentStateStatus = AgentStateStatus.INITIALIZING
    
    # Timestamp when the state was created/updated
    timestamp: float = field(default_factory=time.time)
    
    # Agent-specific conversation history
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Agent-specific metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Agent-specific configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Custom state data for agent-specific state
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the agent state to a dictionary.
        
        Returns:
            Dictionary representation of the agent state
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status.name,
            "timestamp": self.timestamp,
            "conversation_history": self.conversation_history,
            "metadata": self.metadata,
            "config": self.config,
            "custom_data": self.custom_data,
        }
    
    @classmethod
    def from_dict(cls, state_dict: Dict[str, Any]) -> 'AgentState':
        """Create an agent state from a dictionary.
        
        Args:
            state_dict: Dictionary representation of the agent state
            
        Returns:
            AgentState object
        """
        status_str = state_dict.pop("status")
        status = AgentStateStatus[status_str]
        return cls(
            status=status,
            **{k: v for k, v in state_dict.items() if k != "status"}
        )


class StateProvider(abc.ABC):
    """Interface for state persistence providers.
    
    A state provider is responsible for persisting and retrieving agent state.
    Implementations might store state in memory, on disk, or in a database.
    """
    
    @abc.abstractmethod
    async def save_state(self, agent_id: str, state: AgentState) -> None:
        """Save the state of an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            state: Agent state to save
        """
        pass
    
    @abc.abstractmethod
    async def load_state(self, agent_id: str) -> Optional[AgentState]:
        """Load the state of an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            The agent's state, or None if no state is available
        """
        pass
    
    @abc.abstractmethod
    async def delete_state(self, agent_id: str) -> None:
        """Delete the state of an agent.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        pass
    
    @abc.abstractmethod
    async def list_states(self) -> List[str]:
        """List all agent IDs with saved states.
        
        Returns:
            List of agent IDs
        """
        pass


class InMemoryStateProvider(StateProvider):
    """In-memory implementation of a state provider.
    
    This provider stores agent states in memory and is suitable for
    development, testing, or simple production scenarios where persistence
    across process restarts is not required.
    """
    
    def __init__(self):
        """Initialize an in-memory state provider."""
        self._states: Dict[str, AgentState] = {}
    
    async def save_state(self, agent_id: str, state: AgentState) -> None:
        """Save the state of an agent in memory.
        
        Args:
            agent_id: Unique identifier for the agent
            state: Agent state to save
        """
        self._states[agent_id] = state
    
    async def load_state(self, agent_id: str) -> Optional[AgentState]:
        """Load the state of an agent from memory.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            The agent's state, or None if no state is available
        """
        return self._states.get(agent_id)
    
    async def delete_state(self, agent_id: str) -> None:
        """Delete the state of an agent from memory.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        if agent_id in self._states:
            del self._states[agent_id]
    
    async def list_states(self) -> List[str]:
        """List all agent IDs with saved states.
        
        Returns:
            List of agent IDs
        """
        return list(self._states.keys())


class FileStateProvider(StateProvider):
    """File-based implementation of a state provider.
    
    This provider stores agent states as JSON files on disk and is suitable
    for simple production scenarios where persistence across process restarts
    is required.
    """
    
    def __init__(self, directory: str):
        """Initialize a file-based state provider.
        
        Args:
            directory: Directory where state files will be stored
        """
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
    
    async def save_state(self, agent_id: str, state: AgentState) -> None:
        """Save the state of an agent to a file.
        
        Args:
            agent_id: Unique identifier for the agent
            state: Agent state to save
        """
        file_path = os.path.join(self.directory, f"{agent_id}.json")
        
        # Use async file I/O for better performance
        # We use a threadpool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            lambda: self._write_file(file_path, state.to_dict())
        )
    
    def _write_file(self, file_path: str, data: Dict[str, Any]) -> None:
        """Write data to a file.
        
        Args:
            file_path: Path to the file
            data: Data to write
        """
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def load_state(self, agent_id: str) -> Optional[AgentState]:
        """Load the state of an agent from a file.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            The agent's state, or None if no state is available
        """
        file_path = os.path.join(self.directory, f"{agent_id}.json")
        if not os.path.exists(file_path):
            return None
        
        # Use async file I/O for better performance
        loop = asyncio.get_event_loop()
        state_dict = await loop.run_in_executor(
            None, 
            lambda: self._read_file(file_path)
        )
        
        if state_dict:
            return AgentState.from_dict(state_dict)
        return None
    
    def _read_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read data from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Data from the file, or None if the file doesn't exist
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    async def delete_state(self, agent_id: str) -> None:
        """Delete the state of an agent from disk.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        file_path = os.path.join(self.directory, f"{agent_id}.json")
        if os.path.exists(file_path):
            # Use async file I/O for better performance
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: os.remove(file_path))
    
    async def list_states(self) -> List[str]:
        """List all agent IDs with saved states.
        
        Returns:
            List of agent IDs
        """
        # Use async file I/O for better performance
        loop = asyncio.get_event_loop()
        files = await loop.run_in_executor(None, lambda: os.listdir(self.directory))
        
        # Extract agent IDs from filenames
        agent_ids = []
        for file in files:
            if file.endswith('.json'):
                agent_id = file[:-5]  # Remove the .json extension
                agent_ids.append(agent_id)
        
        return agent_ids 