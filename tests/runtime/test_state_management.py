import unittest
import asyncio
import tempfile
import os
import json
from datetime import datetime

from contexa_sdk.runtime.state_management import (
    AgentState,
    AgentStateStatus,
    InMemoryStateProvider,
    FileStateProvider
)

class TestAgentState(unittest.TestCase):
    """Test cases for the AgentState class."""
    
    def test_agent_state_creation(self):
        """Test creating an AgentState instance."""
        agent_state = AgentState(
            agent_id="test-agent-1",
            agent_type="test",
            status=AgentStateStatus.READY,
            timestamp=datetime.now().isoformat(),
            conversation_history=[{"role": "user", "content": "Hello"}],
            metadata={"created_by": "tester"},
            config={"model": "test-model"},
            custom_data={"key": "value"}
        )
        
        self.assertEqual(agent_state.agent_id, "test-agent-1")
        self.assertEqual(agent_state.agent_type, "test")
        self.assertEqual(agent_state.status, AgentStateStatus.READY)
        self.assertEqual(len(agent_state.conversation_history), 1)
        self.assertEqual(agent_state.metadata["created_by"], "tester")
        self.assertEqual(agent_state.config["model"], "test-model")
        self.assertEqual(agent_state.custom_data["key"], "value")
    
    def test_agent_state_to_dict(self):
        """Test converting AgentState to dictionary."""
        timestamp = datetime.now().isoformat()
        agent_state = AgentState(
            agent_id="test-agent-1",
            agent_type="test",
            status=AgentStateStatus.READY,
            timestamp=timestamp,
            conversation_history=[{"role": "user", "content": "Hello"}],
            metadata={"created_by": "tester"},
            config={"model": "test-model"},
            custom_data={"key": "value"}
        )
        
        state_dict = agent_state.to_dict()
        
        self.assertIsInstance(state_dict, dict)
        self.assertEqual(state_dict["agent_id"], "test-agent-1")
        self.assertEqual(state_dict["agent_type"], "test")
        self.assertEqual(state_dict["status"], AgentStateStatus.READY.value)
        self.assertEqual(state_dict["timestamp"], timestamp)
        self.assertEqual(len(state_dict["conversation_history"]), 1)
        self.assertEqual(state_dict["metadata"]["created_by"], "tester")
        self.assertEqual(state_dict["config"]["model"], "test-model")
        self.assertEqual(state_dict["custom_data"]["key"], "value")
    
    def test_agent_state_from_dict(self):
        """Test creating AgentState from dictionary."""
        timestamp = datetime.now().isoformat()
        state_dict = {
            "agent_id": "test-agent-1",
            "agent_type": "test",
            "status": AgentStateStatus.READY.value,
            "timestamp": timestamp,
            "conversation_history": [{"role": "user", "content": "Hello"}],
            "metadata": {"created_by": "tester"},
            "config": {"model": "test-model"},
            "custom_data": {"key": "value"}
        }
        
        agent_state = AgentState.from_dict(state_dict)
        
        self.assertEqual(agent_state.agent_id, "test-agent-1")
        self.assertEqual(agent_state.agent_type, "test")
        self.assertEqual(agent_state.status, AgentStateStatus.READY)
        self.assertEqual(agent_state.timestamp, timestamp)
        self.assertEqual(len(agent_state.conversation_history), 1)
        self.assertEqual(agent_state.metadata["created_by"], "tester")
        self.assertEqual(agent_state.config["model"], "test-model")
        self.assertEqual(agent_state.custom_data["key"], "value")

class TestInMemoryStateProvider(unittest.TestCase):
    """Test cases for the InMemoryStateProvider class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.state_provider = InMemoryStateProvider()
        self.test_state = AgentState(
            agent_id="test-agent-1",
            agent_type="test",
            status=AgentStateStatus.READY,
            timestamp=datetime.now().isoformat(),
            conversation_history=[{"role": "user", "content": "Hello"}],
            metadata={"created_by": "tester"},
            config={"model": "test-model"},
            custom_data={"key": "value"}
        )
    
    async def test_save_and_load_state(self):
        """Test saving and loading state."""
        agent_id = self.test_state.agent_id
        
        # Save state
        await self.state_provider.save_state(self.test_state)
        
        # Load state
        loaded_state = await self.state_provider.load_state(agent_id)
        
        self.assertIsNotNone(loaded_state)
        self.assertEqual(loaded_state.agent_id, agent_id)
        self.assertEqual(loaded_state.agent_type, self.test_state.agent_type)
        self.assertEqual(loaded_state.status, self.test_state.status)
    
    async def test_list_states(self):
        """Test listing states."""
        # Save a state
        await self.state_provider.save_state(self.test_state)
        
        # List states
        states = await self.state_provider.list_states()
        
        self.assertGreaterEqual(len(states), 1)
        self.assertIn(self.test_state.agent_id, [state.agent_id for state in states])
    
    async def test_delete_state(self):
        """Test deleting state."""
        agent_id = self.test_state.agent_id
        
        # Save state
        await self.state_provider.save_state(self.test_state)
        
        # Delete state
        await self.state_provider.delete_state(agent_id)
        
        # Try to load the deleted state
        loaded_state = await self.state_provider.load_state(agent_id)
        
        self.assertIsNone(loaded_state)

class TestFileStateProvider(unittest.TestCase):
    """Test cases for the FileStateProvider class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_provider = FileStateProvider(directory=self.temp_dir)
        self.test_state = AgentState(
            agent_id="test-agent-1",
            agent_type="test",
            status=AgentStateStatus.READY,
            timestamp=datetime.now().isoformat(),
            conversation_history=[{"role": "user", "content": "Hello"}],
            metadata={"created_by": "tester"},
            config={"model": "test-model"},
            custom_data={"key": "value"}
        )
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove all files in temp directory
        for filename in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        
        # Remove the directory
        os.rmdir(self.temp_dir)
    
    async def test_save_and_load_state(self):
        """Test saving and loading state from file."""
        agent_id = self.test_state.agent_id
        
        # Save state
        await self.state_provider.save_state(self.test_state)
        
        # Verify file exists
        file_path = os.path.join(self.temp_dir, f"{agent_id}.json")
        self.assertTrue(os.path.exists(file_path))
        
        # Load state
        loaded_state = await self.state_provider.load_state(agent_id)
        
        self.assertIsNotNone(loaded_state)
        self.assertEqual(loaded_state.agent_id, agent_id)
        self.assertEqual(loaded_state.agent_type, self.test_state.agent_type)
        self.assertEqual(loaded_state.status, self.test_state.status)
    
    async def test_list_states(self):
        """Test listing states from files."""
        # Save a state
        await self.state_provider.save_state(self.test_state)
        
        # Save another state
        second_state = AgentState(
            agent_id="test-agent-2",
            agent_type="test",
            status=AgentStateStatus.RUNNING,
            timestamp=datetime.now().isoformat(),
            conversation_history=[],
            metadata={},
            config={},
            custom_data={}
        )
        await self.state_provider.save_state(second_state)
        
        # List states
        states = await self.state_provider.list_states()
        
        self.assertEqual(len(states), 2)
        agent_ids = [state.agent_id for state in states]
        self.assertIn(self.test_state.agent_id, agent_ids)
        self.assertIn(second_state.agent_id, agent_ids)
    
    async def test_delete_state(self):
        """Test deleting state file."""
        agent_id = self.test_state.agent_id
        
        # Save state
        await self.state_provider.save_state(self.test_state)
        
        # Verify file exists
        file_path = os.path.join(self.temp_dir, f"{agent_id}.json")
        self.assertTrue(os.path.exists(file_path))
        
        # Delete state
        await self.state_provider.delete_state(agent_id)
        
        # Verify file no longer exists
        self.assertFalse(os.path.exists(file_path))
        
        # Try to load the deleted state
        loaded_state = await self.state_provider.load_state(agent_id)
        
        self.assertIsNone(loaded_state)

if __name__ == '__main__':
    unittest.main() 