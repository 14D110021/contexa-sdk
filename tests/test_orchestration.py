"""
Unit tests for the orchestration module components.

This module contains tests for the agent orchestration components:
- Messages and channels
- Task handoffs and protocols
- Shared workspaces and artifacts
- Agent teams
"""

import pytest
from contexa_sdk.orchestration import (
    Message, Channel, HandoffProtocol, TaskHandoff, 
    SharedWorkspace, Artifact, AgentTeam
)
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# Mock agent classes for testing
class MockAgent:
    """Mock agent for testing"""
    def __init__(self, id, name="TestAgent"):
        self.id = id
        self.name = name
        self.input_schemas = {}
        self.allowed_incoming_agents = ["*"]  # Accept from any agent
        
    def process_handoff(self, handoff_data):
        """Process a handoff request"""
        return {
            "status": "success",
            "result": {"processed": True, "input": handoff_data}
        }
        
    def run(self, input_data):
        """Run the agent on input data"""
        return {"result": f"Processed by {self.name}", "input": input_data}

# Test fixtures
@pytest.fixture
def test_message():
    """Create a test message"""
    return Message(
        sender_id="agent1",
        recipient_id="agent2",
        content="Test message",
        message_type="test"
    )

@pytest.fixture
def test_channel():
    """Create a test channel"""
    return Channel(name="test_channel")

@pytest.fixture
def test_agents():
    """Create test agents"""
    return {
        "research": MockAgent(id="research", name="Researcher"),
        "validation": MockAgent(id="validation", name="Validator"),
        "documentation": MockAgent(id="documentation", name="Documenter")
    }

@pytest.fixture
def test_team(test_agents):
    """Create a test team with agents"""
    team = AgentTeam(name="Test Team", expertise=["testing"])
    team.add_agent(test_agents["research"], role="researcher")
    team.add_agent(test_agents["validation"], role="validator")
    return team

@pytest.fixture
def test_workspace():
    """Create a test workspace"""
    return SharedWorkspace(name="Test Workspace")

# Test Message and Channel
class TestMessageSystem:
    """Tests for the message communication system"""
    
    def test_message_creation(self):
        """Test basic message creation and properties"""
        message = Message(
            sender_id="agent1",
            recipient_id="agent2",
            content="Test message",
            message_type="test"
        )
        
        # Verify basic properties
        assert message.sender_id == "agent1"
        assert message.recipient_id == "agent2"
        assert message.content == "Test message"
        assert message.message_type == "test"
        assert message.message_id is not None
        
    def test_message_with_structured_content(self):
        """Test message with dictionary content"""
        content = {"key1": "value1", "key2": 123}
        message = Message(
            sender_id="agent1",
            recipient_id="agent2",
            content=content,
            message_type="data"
        )
        
        # Verify content is preserved
        assert message.content == content
        assert message.content["key1"] == "value1"
        assert message.content["key2"] == 123
        
    def test_channel_message_passing(self):
        """Test sending and receiving messages through a channel"""
        channel = Channel(name="test_channel")
        
        # Create and send messages
        msg1 = Message(sender_id="agent1", recipient_id="agent2", content="Message 1")
        msg2 = Message(sender_id="agent3", recipient_id="agent2", content="Message 2")
        msg3 = Message(sender_id="agent1", recipient_id="agent3", content="Message 3")
        
        channel.send(msg1)
        channel.send(msg2)
        channel.send(msg3)
        
        # Test receiving messages
        agent2_msgs = channel.receive(recipient_id="agent2")
        agent3_msgs = channel.receive(recipient_id="agent3")
        agent4_msgs = channel.receive(recipient_id="agent4")
        
        # Verify correct message routing
        assert len(agent2_msgs) == 2
        assert len(agent3_msgs) == 1
        assert len(agent4_msgs) == 0
        assert agent2_msgs[0].content == "Message 1"
        assert agent2_msgs[1].content == "Message 2"
        assert agent3_msgs[0].content == "Message 3"
        
    def test_channel_filtering_by_timestamp(self):
        """Test channel filtering by timestamp"""
        channel = Channel()
        
        # Send a first batch of messages
        msg1 = Message(sender_id="agent1", recipient_id="agent2", content="Message 1")
        channel.send(msg1)
        
        # Record timestamp
        timestamp_after_first = msg1.timestamp
        
        # Send more messages
        msg2 = Message(sender_id="agent1", recipient_id="agent2", content="Message 2")
        channel.send(msg2)
        
        # Test filtering by timestamp
        recent_msgs = channel.receive(recipient_id="agent2", since_timestamp=timestamp_after_first)
        
        # Should only get the second message
        assert len(recent_msgs) == 1
        assert recent_msgs[0].content == "Message 2"

# Test Handoff Protocol
class TestHandoffProtocol:
    """Tests for the handoff protocol system"""
    
    def test_protocol_with_schemas(self):
        """Test protocol with Pydantic schemas"""
        # Define test schemas
        class InputSchema(BaseModel):
            field1: str
            field2: int = Field(ge=0)
            
        class OutputSchema(BaseModel):
            result: bool
            message: str
            
        # Create protocol
        protocol = HandoffProtocol(
            name="test_protocol",
            input_schema=InputSchema,
            output_schema=OutputSchema
        )
        
        # Test input validation - valid
        valid_input = {"field1": "test", "field2": 10}
        validated = protocol.validate_input(valid_input)
        assert validated.field1 == "test"
        assert validated.field2 == 10
        
        # Test input validation - invalid (should raise validation error)
        invalid_input = {"field1": "test", "field2": -5}
        with pytest.raises(Exception):
            protocol.validate_input(invalid_input)
            
        # Test output validation - valid
        valid_output = {"result": True, "message": "Success"}
        validated = protocol.validate_output(valid_output)
        assert validated.result is True
        assert validated.message == "Success"
        
        # Test output validation - invalid (should raise validation error)
        invalid_output = {"result": "true", "message": 123}  # Wrong types
        with pytest.raises(Exception):
            protocol.validate_output(invalid_output)
            
    def test_protocol_without_schemas(self):
        """Test protocol without schemas (passthrough)"""
        protocol = HandoffProtocol(name="simple_protocol")
        
        # Should pass through data without validation
        input_data = {"any": "data"}
        result = protocol.validate_input(input_data)
        assert result == input_data

# Test TaskHandoff
class TestTaskHandoff:
    """Tests for the task handoff system"""
    
    def test_basic_handoff(self, test_agents):
        """Test basic task handoff between agents"""
        # Create handoff
        handoff = TaskHandoff(
            sender=test_agents["research"],
            recipient=test_agents["validation"],
            task_description="Test task",
            input_data={"test": "data"}
        )
        
        # Execute handoff
        result = handoff.execute()
        
        # Verify results
        assert handoff.status == "completed"
        assert result["status"] == "completed"
        assert handoff.result["processed"] is True
        assert "input" in handoff.result
        assert handoff.result["input"]["task_description"] == "Test task"
        
    def test_handoff_with_protocol(self, test_agents):
        """Test handoff with validation protocol"""
        # Define schema
        class TestSchema(BaseModel):
            field1: str
            field2: int
            
        # Create protocol with schema
        protocol = HandoffProtocol(
            name="test_protocol",
            input_schema=TestSchema,
            output_schema=None  # No output validation
        )
        
        # Create handoff with valid data
        handoff = TaskHandoff(
            sender=test_agents["research"],
            recipient=test_agents["validation"],
            task_description="Valid test",
            input_data={"field1": "test", "field2": 42},
            protocol=protocol
        )
        
        # Execute handoff
        result = handoff.execute()
        
        # Verify success
        assert handoff.status == "completed"
        assert result["status"] == "completed"
        
    def test_handoff_with_invalid_data(self, test_agents):
        """Test handoff with invalid data against protocol"""
        # Define schema
        class TestSchema(BaseModel):
            field1: str
            field2: int = Field(ge=0)
            
        # Create protocol with schema
        protocol = HandoffProtocol(
            name="test_protocol",
            input_schema=TestSchema
        )
        
        # Create handoff with invalid data
        handoff = TaskHandoff(
            sender=test_agents["research"],
            recipient=test_agents["validation"],
            task_description="Invalid test",
            input_data={"field1": "test", "field2": -1},  # Invalid negative value
            protocol=protocol
        )
        
        # Execute handoff (should fail validation)
        result = handoff.execute()
        
        # Verify failure
        assert handoff.status == "failed"
        assert result["status"] == "failed"
        assert "validation failed" in str(result["error"]).lower()

# Test SharedWorkspace
class TestSharedWorkspace:
    """Tests for the shared workspace system"""
    
    def test_artifact_creation(self, test_workspace):
        """Test creating artifacts in workspace"""
        # Add artifact
        artifact_id = test_workspace.add_artifact(
            name="Test Document",
            content={"data": "test content"},
            creator_id="agent1",
            artifact_type="document"
        )
        
        # Verify artifact was created
        assert artifact_id in test_workspace.artifacts
        assert test_workspace.artifacts[artifact_id].name == "Test Document"
        assert test_workspace.artifacts[artifact_id].creator_id == "agent1"
        assert test_workspace.artifacts[artifact_id].version == 1
        
    def test_artifact_updates(self, test_workspace):
        """Test updating artifacts and version history"""
        # Create artifact
        artifact_id = test_workspace.add_artifact(
            name="Versioned Doc",
            content={"version": 1, "data": "initial"},
            creator_id="agent1"
        )
        
        # Update artifact
        test_workspace.update_artifact(
            artifact_id=artifact_id,
            content={"version": 2, "data": "updated"},
            editor_id="agent2",
            comment="First update"
        )
        
        # Update again
        test_workspace.update_artifact(
            artifact_id=artifact_id,
            content={"version": 3, "data": "final"},
            editor_id="agent3",
            comment="Final update"
        )
        
        # Get current version
        artifact = test_workspace.get_artifact(artifact_id)
        
        # Verify current state
        assert artifact["version"] == 3
        assert artifact["content"]["data"] == "final"
        
        # Verify history
        history = test_workspace.artifacts[artifact_id].version_history
        assert len(history) == 2  # Two prior versions
        assert history[0]["version"] == 1
        assert history[0]["content"]["data"] == "initial"
        assert history[1]["version"] == 2
        assert history[1]["content"]["data"] == "updated"
        
        # Verify activities were logged
        assert len(test_workspace.activities) == 3  # Create + 2 updates
        assert test_workspace.activities[0]["action"] == "create_artifact"
        assert test_workspace.activities[1]["action"] == "update_artifact"
        assert test_workspace.activities[2]["action"] == "update_artifact"
        
    def test_get_artifact_history(self, test_workspace):
        """Test retrieving artifact history"""
        # Create and update artifact
        artifact_id = test_workspace.add_artifact(
            name="History Test",
            content={"v": 1},
            creator_id="agent1"
        )
        
        test_workspace.update_artifact(
            artifact_id=artifact_id,
            content={"v": 2},
            editor_id="agent2"
        )
        
        # Get history
        history = test_workspace.get_artifact_history(artifact_id)
        
        # Verify history
        assert len(history) == 2  # Initial + current
        assert history[0]["version"] == 1
        assert history[0]["content"]["v"] == 1
        assert history[1]["version"] == 2
        assert history[1]["content"]["v"] == 2
        
    def test_get_specific_version(self, test_workspace):
        """Test retrieving specific artifact version"""
        # Create and update artifact
        artifact_id = test_workspace.add_artifact(
            name="Version Test",
            content={"v": 1, "data": "original"},
            creator_id="agent1"
        )
        
        test_workspace.update_artifact(
            artifact_id=artifact_id,
            content={"v": 2, "data": "updated"},
            editor_id="agent2"
        )
        
        # Get specific version
        v1 = test_workspace.get_artifact(artifact_id, version=1)
        v2 = test_workspace.get_artifact(artifact_id)  # Current version
        
        # Verify versions
        assert v1["version"] == 1
        assert v1["content"]["data"] == "original"
        assert v2["version"] == 2
        assert v2["content"]["data"] == "updated"
        
    def test_invalid_artifact_access(self, test_workspace):
        """Test error handling for invalid artifact access"""
        # Try to get non-existent artifact
        with pytest.raises(ValueError):
            test_workspace.get_artifact("nonexistent_id")
            
        # Create artifact and try to get invalid version
        artifact_id = test_workspace.add_artifact(
            name="Test",
            content={"data": "test"},
            creator_id="agent1"
        )
        
        with pytest.raises(ValueError):
            # Try to get version that doesn't exist
            test_workspace.get_artifact(artifact_id, version=99)

# Test AgentTeam
class TestAgentTeam:
    """Tests for the agent team system"""
    
    def test_team_creation(self, test_agents):
        """Test creating a team with agents"""
        team = AgentTeam(
            name="Research Team",
            expertise=["research", "analysis"]
        )
        
        # Add agents
        team.add_agent(test_agents["research"], role="lead")
        team.add_agent(test_agents["validation"], role="member")
        
        # Verify team state
        assert team.name == "Research Team"
        assert "research" in team.expertise
        assert len(team.member_agents) == 2
        assert team.member_agents[0]["role"] == "lead"
        assert team.member_agents[1]["role"] == "member"
        
    def test_get_agents_by_role(self, test_team):
        """Test getting agents by role"""
        # Add another agent with same role
        researcher2 = MockAgent(id="researcher2", name="Assistant Researcher")
        test_team.add_agent(researcher2, role="researcher")
        
        # Get agents by role
        researchers = test_team.get_agents_by_role("researcher")
        validators = test_team.get_agents_by_role("validator")
        nonexistent = test_team.get_agents_by_role("nonexistent")
        
        # Verify results
        assert len(researchers) == 2
        assert len(validators) == 1
        assert len(nonexistent) == 0
        
    def test_remove_agent(self, test_team):
        """Test removing an agent from a team"""
        # Verify initial state
        assert len(test_team.member_agents) == 2
        
        # Remove an agent
        result = test_team.remove_agent("research")
        
        # Verify agent was removed
        assert result is True
        assert len(test_team.member_agents) == 1
        
        # Try to remove non-existent agent
        result = test_team.remove_agent("nonexistent")
        assert result is False
        
    def test_task_assignment(self, test_team):
        """Test assigning tasks to a team"""
        # Set a lead agent
        test_team.lead_agent = test_team.member_agents[0]["agent"]
        
        # Assign task
        result = test_team.assign_task({"task": "Test task"})
        
        # Verify task was processed by the lead agent
        assert "result" in result
        assert "Processed by" in result["result"] 