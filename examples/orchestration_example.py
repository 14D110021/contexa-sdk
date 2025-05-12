"""
Example demonstrating Contexa SDK's orchestration capabilities.

This example shows how to use the orchestration module to create a multi-agent
system with structured communication, task handoffs, and shared workspaces.
"""

from contexa_sdk.orchestration import (
    Message, Channel, HandoffProtocol, TaskHandoff,
    SharedWorkspace, Artifact, AgentTeam
)
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# Define mock agents for the example
class MockAgent:
    """Mock agent for the example"""
    def __init__(self, id, name, expertise=None):
        self.id = id
        self.name = name
        self.expertise = expertise or []
        self.allowed_incoming_agents = ["*"]  # Allow all agents to send tasks
        
    def process_handoff(self, handoff_data):
        """Process a task handoff"""
        print(f"{self.name} received task: {handoff_data['task_description']}")
        
        # Simulate processing
        if self.id == "research":
            return {
                "status": "completed",
                "result": {
                    "findings": [
                        {"topic": "Quantum Computing", "relevance": 0.9},
                        {"topic": "Medical Applications", "relevance": 0.8}
                    ],
                    "confidence": 0.85
                }
            }
        elif self.id == "validation":
            return {
                "status": "completed",
                "result": {
                    "is_valid": True,
                    "comments": "Findings appear accurate and well-supported",
                    "score": 0.9
                }
            }
        elif self.id == "documentation":
            return {
                "status": "completed",
                "result": {
                    "document": "Final research document with validated findings",
                    "sections": ["Introduction", "Methodology", "Findings", "Conclusion"]
                }
            }
        
        return {"status": "completed", "result": {"processed": True}}
        
    def run(self, input_data):
        """Run the agent on input data"""
        print(f"{self.name} running with input: {input_data}")
        return self.process_handoff({"task_description": "Generic task", "input_data": input_data})


def demonstrate_messaging():
    """Demonstrate agent messaging capabilities"""
    print("\n=== MESSAGING DEMONSTRATION ===\n")
    
    # Create a communication channel
    channel = Channel(name="research_team")
    
    # Send some messages
    print("Sending messages...")
    msg1 = Message(
        sender_id="research",
        recipient_id="validation",
        content="Please review these research findings",
        message_type="request",
        metadata={"priority": "high"}
    )
    channel.send(msg1)
    
    msg2 = Message(
        sender_id="lead",
        recipient_id="research",
        content={"topic": "Quantum computing", "focus": "medical applications"},
        message_type="research_directive"
    )
    channel.send(msg2)
    
    # Broadcast a message to all team members
    recipients = ["research", "validation", "documentation"]
    channel.broadcast(
        sender_id="lead",
        recipient_ids=recipients,
        content="Team meeting at 3pm to discuss progress",
        message_type="announcement"
    )
    
    # Receive messages
    print("\nMessages for validation agent:")
    validation_msgs = channel.receive(recipient_id="validation")
    for msg in validation_msgs:
        print(f"From: {msg.sender_id}, Type: {msg.message_type}")
        print(f"Content: {msg.content}")
        print()
    
    print("Messages for research agent:")
    research_msgs = channel.receive(recipient_id="research")
    for msg in research_msgs:
        print(f"From: {msg.sender_id}, Type: {msg.message_type}")
        print(f"Content: {msg.content}")
        print()


def demonstrate_handoffs(agents):
    """Demonstrate task handoffs between agents"""
    print("\n=== HANDOFF DEMONSTRATION ===\n")
    
    # Define schemas for handoffs
    class ResearchFindings(BaseModel):
        findings: List[Dict[str, Any]]
        confidence: float = Field(ge=0.0, le=1.0)
        
    class ValidationResult(BaseModel):
        is_valid: bool
        comments: str
        score: float = Field(ge=0.0, le=1.0)
    
    # Create a protocol for research to validation handoff
    validation_protocol = HandoffProtocol(
        name="research_validation_protocol",
        input_schema=ResearchFindings,
        output_schema=ValidationResult,
        description="Protocol for validating research findings"
    )
    
    # Execute a research task
    print("Executing research task...")
    research_result = agents["research"].run({"topic": "Quantum computing in medicine"})
    
    # Create and execute a validation handoff
    print("\nExecuting validation handoff...")
    validation_handoff = TaskHandoff(
        sender=agents["research"],
        recipient=agents["validation"],
        task_description="Validate research findings on quantum computing",
        input_data={
            "findings": research_result["result"]["findings"],
            "confidence": research_result["result"]["confidence"]
        },
        protocol=validation_protocol
    )
    
    validation_result = validation_handoff.execute()
    print(f"Validation result: {validation_result}")
    
    # Create and execute a documentation handoff
    print("\nExecuting documentation handoff...")
    documentation_handoff = TaskHandoff(
        sender=agents["validation"],
        recipient=agents["documentation"],
        task_description="Create final document from validated research",
        input_data={
            "research": research_result["result"],
            "validation": validation_result["result"]
        }
    )
    
    documentation_result = documentation_handoff.execute()
    print(f"Documentation result: {documentation_result}")


def demonstrate_workspace():
    """Demonstrate shared workspace capabilities"""
    print("\n=== WORKSPACE DEMONSTRATION ===\n")
    
    # Create a workspace
    workspace = SharedWorkspace(name="Research Project")
    
    # Add some artifacts
    print("Adding artifacts to workspace...")
    doc_id = workspace.add_artifact(
        name="Research Findings",
        content={
            "title": "Quantum Computing in Medicine",
            "abstract": "Initial findings on quantum computing applications in medicine",
            "sections": ["Introduction", "Background", "Methodology"]
        },
        creator_id="research",
        artifact_type="document"
    )
    
    data_id = workspace.add_artifact(
        name="Research Data",
        content={
            "datasets": ["quantum_simulations.csv", "medical_outcomes.json"],
            "sample_size": 500
        },
        creator_id="research",
        artifact_type="dataset"
    )
    
    # Update an artifact
    print("\nUpdating research document...")
    workspace.update_artifact(
        artifact_id=doc_id,
        content={
            "title": "Quantum Computing in Medicine",
            "abstract": "Comprehensive analysis of quantum computing applications in medicine",
            "sections": ["Introduction", "Background", "Methodology", "Findings", "Discussion"],
            "validated": True
        },
        editor_id="validation",
        comment="Added validation results and expanded sections"
    )
    
    # Get artifact and history
    print("\nRetrieving artifact information:")
    document = workspace.get_artifact(doc_id)
    print(f"Current document: {document['name']}, version: {document['version']}")
    print(f"Sections: {document['content']['sections']}")
    
    history = workspace.get_artifact_history(doc_id)
    print(f"\nDocument history: {len(history)} versions")
    for version in history:
        print(f"Version {version['version']}: {len(version['content']['sections'])} sections")
    
    # Search for artifacts
    print("\nSearching for artifacts:")
    datasets = workspace.get_artifacts_by_type("dataset")
    print(f"Found {len(datasets)} datasets")
    
    # View workspace activity
    print("\nWorkspace activities:")
    for i, activity in enumerate(workspace.activities):
        print(f"{i+1}. {activity['action']} at {activity['timestamp']}")


def demonstrate_team(agents):
    """Demonstrate team capabilities"""
    print("\n=== TEAM DEMONSTRATION ===\n")
    
    # Create a research team
    team = AgentTeam(
        name="Quantum Medical Research Team",
        expertise=["quantum computing", "medical research", "documentation"]
    )
    
    # Add agents to the team
    print("Adding agents to the team...")
    team.add_agent(agents["research"], role="lead_researcher")
    team.add_agent(agents["validation"], role="validation_specialist")
    team.add_agent(agents["documentation"], role="documentation_specialist")
    
    # Get agents by role
    print("\nTeam composition:")
    leads = team.get_agents_by_role("lead_researcher")
    validators = team.get_agents_by_role("validation_specialist")
    documenters = team.get_agents_by_role("documentation_specialist")
    
    print(f"Lead researchers: {len(leads)}")
    print(f"Validation specialists: {len(validators)}")
    print(f"Documentation specialists: {len(documenters)}")
    
    # Assign a task to the team
    print("\nAssigning task to the team...")
    result = team.assign_task({
        "research_topic": "Quantum algorithms for drug discovery",
        "deadline": "2023-12-15",
        "priority": "high"
    })
    
    print(f"Task assignment result: {result}")


def main():
    """Main function to run the demonstration"""
    print("=== CONTEXA SDK ORCHESTRATION DEMONSTRATION ===")
    
    # Create mock agents
    agents = {
        "lead": MockAgent(id="lead", name="Team Lead", expertise=["project management"]),
        "research": MockAgent(id="research", name="Research Agent", expertise=["data analysis"]),
        "validation": MockAgent(id="validation", name="Validation Agent", expertise=["verification"]),
        "documentation": MockAgent(id="documentation", name="Documentation Agent", expertise=["writing"])
    }
    
    # Run the demonstrations
    demonstrate_messaging()
    demonstrate_handoffs(agents)
    demonstrate_workspace()
    demonstrate_team(agents)
    
    print("\n=== DEMONSTRATION COMPLETE ===")


if __name__ == "__main__":
    main() 