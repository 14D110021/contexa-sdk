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
    persisted and restored. It captures all necessary information to reconstruct
    an agent's runtime state, including conversation history, configuration,
    and custom state data.
    
    The state includes standard fields like agent ID, type, and status, as well
    as flexible containers for conversation history, metadata, configuration,
    and custom data specific to particular agent implementations.
    
    Attributes:
        agent_id: Unique identifier for the agent
        agent_type: Type of the agent (e.g., "search", "conversation", "task")
        status: Current operational status of the agent
        timestamp: Unix timestamp when this state was created/updated
        conversation_history: List of interaction records (messages, tool calls, etc.)
        metadata: Additional descriptive information about the agent
        config: Configuration parameters for the agent
        custom_data: Flexible container for agent-specific state information
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
        """Convert the agent state to a serializable dictionary.
        
        Transforms the AgentState object into a plain dictionary that can be
        easily serialized to JSON or other formats for persistence. This method
        handles the conversion of enum values to strings and ensures all data
        is in a serializable format.
        
        Returns:
            Dictionary representation of the agent state with all fields,
            where the status enum is converted to its string name.
            
        Note:
            This method does not perform deep validation of whether all contained
            objects are actually serializable. If custom_data or other fields contain
            complex objects, they should be converted to serializable types before
            being added to the AgentState.
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
        """Create an agent state from a dictionary representation.
        
        Reconstructs an AgentState object from a dictionary, typically one that
        was previously created by the to_dict method. This method handles the
        conversion of string status names back to enum values.
        
        Args:
            state_dict: Dictionary representation of the agent state, containing
                all required fields. The 'status' field should be a string
                matching one of the AgentStateStatus enum names.
            
        Returns:
            A new AgentState object initialized with the values from the dictionary
            
        Raises:
            KeyError: If required fields are missing from the dictionary
            ValueError: If the status string doesn't match any AgentStateStatus enum name
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
    is required. Each agent's state is stored in a separate JSON file named
    with the agent's ID.
    
    The provider uses asynchronous file I/O operations to avoid blocking the
    event loop when reading or writing state files, making it suitable for
    high-throughput applications.
    
    Attributes:
        directory: The directory path where state files are stored
    """
    
    def __init__(self, directory: str):
        """Initialize a file-based state provider.
        
        Creates the storage directory if it doesn't exist.
        
        Args:
            directory: Directory path where state files will be stored.
                Each agent's state will be stored in a separate file
                named '{agent_id}.json' within this directory.
                
        Raises:
            PermissionError: If the directory cannot be created due to
                insufficient permissions
            OSError: If there are other OS-level errors creating the directory
        """
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
    
    async def save_state(self, agent_id: str, state: AgentState) -> None:
        """Save the state of an agent to a file.
        
        Writes the agent's state to a JSON file named '{agent_id}.json'
        in the configured directory. This operation is performed asynchronously
        to avoid blocking the event loop.
        
        Args:
            agent_id: Unique identifier for the agent
            state: Agent state to save
            
        Raises:
            OSError: If the file cannot be written due to I/O errors
            PermissionError: If the file cannot be written due to permissions
            TypeError: If the state contains objects that cannot be serialized to JSON
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
        
        Helper method to write data to a file synchronously. This method is
        intended to be called within a thread pool executor to avoid blocking
        the main event loop.
        
        Args:
            file_path: Path to the file to write
            data: Dictionary data to serialize and write as JSON
            
        Raises:
            OSError: If the file cannot be written due to I/O errors
            PermissionError: If the file cannot be written due to permissions
            TypeError: If the data contains objects that cannot be serialized to JSON
        """
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def load_state(self, agent_id: str) -> Optional[AgentState]:
        """Load the state of an agent from a file.
        
        Reads the agent's state from a JSON file named '{agent_id}.json'
        in the configured directory. This operation is performed asynchronously
        to avoid blocking the event loop.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            The agent's state object if the file exists and contains valid data,
            or None if the file doesn't exist or contains invalid data
            
        Raises:
            OSError: If there are I/O errors reading the file (other than FileNotFound)
            PermissionError: If the file cannot be read due to permissions
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
            try:
                return AgentState.from_dict(state_dict)
            except (KeyError, ValueError) as e:
                # Log the error and return None for invalid state data
                print(f"Error loading state for agent {agent_id}: {str(e)}")
                return None
        return None
    
    def _read_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Read data from a file.
        
        Helper method to read and parse JSON data from a file synchronously.
        This method is intended to be called within a thread pool executor
        to avoid blocking the main event loop.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Dictionary containing the parsed JSON data, or None if the file
            doesn't exist or contains invalid JSON
            
        Raises:
            OSError: If there are I/O errors reading the file (other than FileNotFound)
            PermissionError: If the file cannot be read due to permissions
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            # Return None for invalid JSON instead of raising an exception
            print(f"Invalid JSON in file {file_path}")
            return None
    
    async def delete_state(self, agent_id: str) -> None:
        """Delete the state of an agent from disk.
        
        Removes the agent's state file if it exists. This operation is performed
        asynchronously to avoid blocking the event loop.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Raises:
            OSError: If the file cannot be deleted due to I/O errors
            PermissionError: If the file cannot be deleted due to permissions
        """
        file_path = os.path.join(self.directory, f"{agent_id}.json")
        if os.path.exists(file_path):
            # Use async file I/O for better performance
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: os.remove(file_path))
    
    async def list_states(self) -> List[str]:
        """List all agent IDs with saved states.
        
        Scans the storage directory for JSON files and extracts agent IDs
        from the filenames. This operation is performed asynchronously to
        avoid blocking the event loop.
        
        Returns:
            List of agent IDs that have saved states
            
        Raises:
            OSError: If the directory cannot be read due to I/O errors
            PermissionError: If the directory cannot be read due to permissions
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