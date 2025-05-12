# Agent Orchestration in Contexa SDK

This document explains how Contexa SDK enables multi-agent orchestration, communication, and collaboration while maintaining framework interoperability.

## Overview

Contexa SDK's orchestration system allows you to build sophisticated agent workflows where multiple specialized agents collaborate on complex tasks. The system is designed to:

1. Work with Contexa's core "write once, run anywhere" philosophy
2. Enable cross-framework agent collaboration
3. Provide structured patterns for agent interactions

## Core Components

### Messages and Channels

Messages represent direct communication between agents:

```python
from contexa_sdk.orchestration import Message, Channel

# Create a communication channel
channel = Channel(name="team_channel")

# Agent 1 sends a message to Agent 2
message = Message(
    sender_id="research_agent",
    recipient_id="validation_agent",
    content="Please validate the research findings",
    message_type="request",
    metadata={"priority": "high"}
)
channel.send(message)

# Agent 2 receives its messages
messages = channel.receive(recipient_id="validation_agent")
```

### Task Handoffs

Task handoffs represent formal work transfers between agents with validation:

```python
from contexa_sdk.orchestration import TaskHandoff, HandoffProtocol
from pydantic import BaseModel, Field
from typing import List, Dict

# Define schemas for the handoff
class ResearchFindings(BaseModel):
    topic: str
    findings: List[Dict]
    confidence: float = Field(ge=0.0, le=1.0)
    
class ValidationResult(BaseModel):
    is_valid: bool
    comments: str
    score: float = Field(ge=0.0, le=1.0)

# Create a protocol with these schemas
protocol = HandoffProtocol(
    name="validation_protocol",
    input_schema=ResearchFindings,
    output_schema=ValidationResult
)

# Create and execute a handoff
handoff = TaskHandoff(
    sender=research_agent,
    recipient=validation_agent,
    task_description="Validate research on quantum computing",
    input_data={
        "topic": "Quantum Computing",
        "findings": [{"id": 1, "text": "Finding 1"}, {"id": 2, "text": "Finding 2"}],
        "confidence": 0.85
    },
    protocol=protocol
)

result = handoff.execute()
```

### Shared Workspaces

Shared workspaces enable collaborative work on documents and data:

```python
from contexa_sdk.orchestration import SharedWorkspace

# Create a workspace
workspace = SharedWorkspace(name="Research Project")

# Agent 1 adds a document
doc_id = workspace.add_artifact(
    name="Research Findings",
    content={"topic": "Quantum Computing", "findings": [...]},
    creator_id="research_agent"
)

# Agent 2 updates the document
workspace.update_artifact(
    artifact_id=doc_id,
    content={"topic": "Quantum Computing", "findings": [...], "validated": True},
    editor_id="validation_agent",
    comment="Validated findings and added references"
)

# Get document history
document = workspace.get_artifact(doc_id)
versions = workspace.get_artifact_history(doc_id)
```

### Agent Teams

Teams organize agents into functional groups:

```python
from contexa_sdk.orchestration import AgentTeam

# Create a research team
research_team = AgentTeam(
    name="Research Team",
    expertise=["quantum computing", "medical research"]
)

# Add agents to the team
research_team.add_agent(researcher_agent, role="lead")
research_team.add_agent(assistant_researcher, role="specialist")
research_team.add_agent(validation_agent, role="validator")
```

## Framework Interoperability

Contexa's orchestration system is designed to work seamlessly with all supported agent frameworks. While each framework has its own approach to agent interactions, Contexa provides a unified layer that can be adapted to work with:

### LangChain Integration

The orchestration components can be used with LangChain agents:

```python
from contexa_sdk.adapters.langchain import convert_agent
from contexa_sdk.orchestration import TaskHandoff

# Convert Contexa agents to LangChain agents
lc_agent1 = convert_agent(contexa_agent1)
lc_agent2 = convert_agent(contexa_agent2)

# Use orchestration with LangChain agents
handoff = TaskHandoff(
    sender=contexa_agent1,
    recipient=contexa_agent2,
    task_description="Analyze this data",
    input_data={"dataset": "customer_data.csv"}
)

# The recipient can be a LangChain native agent
# Contexa handles the conversion behind the scenes
result = handoff.execute()
```

### CrewAI Integration

CrewAI's native team-based approach works well with Contexa's orchestration:

```python
from contexa_sdk.adapters.crewai import convert_team
from contexa_sdk.orchestration import AgentTeam

# Create a Contexa team
team = AgentTeam(name="Research Team")
team.add_agent(researcher_agent, role="researcher")
team.add_agent(writer_agent, role="writer")

# Convert to CrewAI crew
crew = convert_team(team)

# Use with CrewAI's native functionality
result = crew.kickoff()
```

### OpenAI Agents SDK Integration

Contexa orchestration works with OpenAI's Assistants API:

```python
from contexa_sdk.adapters.openai import convert_agent
from contexa_sdk.orchestration import SharedWorkspace

# Create a shared workspace for collaboration
workspace = SharedWorkspace(name="Customer Support")

# Convert Contexa agents to OpenAI assistants
openai_assistant = convert_agent(contexa_agent)

# Agents can collaborate via the workspace
artifact_id = workspace.add_artifact(
    name="Customer Inquiry",
    content={"query": "How do I reset my password?"},
    creator_id="support_agent"
)

# OpenAI assistant can access the workspace
response = openai_assistant.run({"workspace_artifact": artifact_id})
```

### Google ADK Integration

The orchestration system also works with Google's Agent Development Kit:

```python
from contexa_sdk.adapters.google_adk import convert_agent
from contexa_sdk.orchestration import Message, Channel

# Set up a communication channel
channel = Channel(name="support_channel")

# Convert Contexa agents to Google ADK agents
adk_agent = convert_agent(contexa_agent)

# Use messaging with ADK agents
channel.send(Message(
    sender_id="user",
    recipient_id="adk_agent",
    content="Can you help me with my account?"
))

# ADK agent receives and processes messages
messages = channel.receive(recipient_id="adk_agent")
```

## Use Cases

### Research and Validation Workflow

A common pattern is the research-validation-documentation workflow:

1. **Research Agent** gathers information on a topic
2. **Validation Agent** verifies the accuracy and completeness
3. **Documentation Agent** creates the final polished output

```python
# Define the workflow with handoffs
research_findings = research_agent.run(research_query)

validation_handoff = TaskHandoff(
    sender=research_agent,
    recipient=validation_agent,
    task_description="Validate these research findings",
    input_data=research_findings
)
validation_result = validation_handoff.execute()

if validation_result["status"] == "completed":
    documentation_handoff = TaskHandoff(
        sender=validation_agent,
        recipient=documentation_agent,
        task_description="Create final report",
        input_data=validation_result["result"]
    )
    final_document = documentation_handoff.execute()
```

### Cross-Framework Collaboration

One of the most powerful use cases is enabling agents from different frameworks to collaborate:

```python
# LangChain agent for research
langchain_researcher = langchain_adapter.convert_agent(research_agent)

# CrewAI agent for analysis
crewai_analyst = crewai_adapter.convert_agent(analysis_agent)

# OpenAI agent for documentation
openai_writer = openai_adapter.convert_agent(documentation_agent)

# Create a cross-framework team
team = AgentTeam(name="Cross-Framework Team")
team.add_agent(langchain_researcher, role="researcher")
team.add_agent(crewai_analyst, role="analyst") 
team.add_agent(openai_writer, role="writer")

# Set up communication and workspace
channel = Channel(name="team_channel")
workspace = SharedWorkspace(name="Cross-Framework Project")

# Now these agents from different frameworks can collaborate
# using Contexa's orchestration layer
```

## Best Practices

1. **Define Clear Schemas**
   
   Always define input and output schemas for handoffs to ensure agents can properly validate and process data.

2. **Use Specialized Agents**
   
   Create agents with specialized skills rather than trying to build a single all-purpose agent.

3. **Implement Error Handling**
   
   Add callbacks to handoffs to handle failures and retry logic.

4. **Version Control Artifacts**
   
   Use the shared workspace's versioning capabilities to keep track of document evolution.

5. **Maintain Framework Compatibility**
   
   When using orchestration with multiple frameworks, ensure you're using the appropriate adapters.

## Integration with MCP

The orchestration components can be exposed via the Model Context Protocol (MCP), enabling remote agents to participate in collaborative workflows:

```python
from contexa_sdk.mcp import expose_as_mcp
from contexa_sdk.orchestration import AgentTeam

# Create a team
team = AgentTeam(name="MCP Team")
team.add_agent(researcher, role="researcher")
team.add_agent(writer, role="writer")

# Expose the team as an MCP endpoint
mcp_endpoint = expose_as_mcp(team, endpoint="/teams/research")

# Now this team can be accessed remotely via the MCP protocol
# allowing for distributed agent orchestration
```

## Conclusion

The orchestration module adds powerful collaboration capabilities to Contexa SDK while maintaining its core mission of framework interoperability. By providing structured patterns for agent interactions, it enables sophisticated multi-agent workflows that can span across different frameworks and deployment environments. 