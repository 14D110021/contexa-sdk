"""
Example demonstrating MCP-compatible agent handoffs and communication.

This example shows how to:
1. Create MCP-compatible agents
2. Register existing ContexaAgents with the MCP registry
3. Perform handoffs between agents using the MCP protocol
4. Use streaming responses for real-time updates
5. Define capability-based agent discovery

This standardized approach to agent communication is based on principles
from Anthropic's Model Context Protocol (MCP) and inspired by IBM's 
Agent Communication Protocol (ACP).
"""

import asyncio
import uuid
import json
import time
import os
import sys
from typing import Dict, List, Any, Optional, AsyncIterator

# Add the parent directory to the path so we can import the SDK
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import core Contexa components
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool

# Import MCP components
from contexa_sdk.orchestration.mcp_agent import (
    MCPAgent, MessageEnvelope, AgentState, registry, broker
)
from contexa_sdk.orchestration.mcp_handoff import (
    handoff, register_contexa_agent
)

# Define some tools
@ContexaTool.register(
    name="research_web",
    description="Search the web for information"
)
async def research_web(query: str) -> str:
    """Simulate web search."""
    # In a real implementation, this would call an actual search API
    await asyncio.sleep(1)  # Simulate network delay
    return f"Research results for '{query}': Found relevant information about {query}."


@ContexaTool.register(
    name="analyze_text",
    description="Analyze text for sentiment and key points"
)
async def analyze_text(text: str) -> Dict[str, Any]:
    """Analyze text content."""
    # Simulate text analysis
    await asyncio.sleep(0.5)
    return {
        "sentiment": "positive",
        "key_points": ["point 1", "point 2", "point 3"],
        "word_count": len(text.split())
    }


@ContexaTool.register(
    name="generate_report",
    description="Generate a formatted report from data"
)
async def generate_report(title: str, content: Dict[str, Any]) -> str:
    """Generate a report from content."""
    # Simulate report generation
    await asyncio.sleep(0.5)
    sections = content.get("sections", [])
    section_text = "\n".join([f"## {section}" for section in sections])
    return f"# {title}\n\n{section_text}\n\nGenerated at {time.ctime()}"


# Create an MCP-native agent
def create_research_agent() -> MCPAgent:
    """Create a native MCP-compatible research agent."""
    print("📚 Creating MCP-native Research Agent...")
    
    agent = MCPAgent(
        agent_id="research-agent",
        name="Research Agent",
        description="Finds and summarizes information on topics",
        version="1.0.0",
        capabilities=["research", "summarization"],
        accepts_streaming=False,
        produces_streaming=True,
        metadata={
            "creator": "Contexa SDK",
            "specialty": "information gathering"
        }
    )
    
    # Define execution handler
    def execution_handler(content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle research requests."""
        query = content.get("input_data", {}).get("query", "")
        if not query:
            return {
                "error": "Missing query parameter",
                "code": "missing_parameter"
            }
        
        # Simulate research processing
        return {
            "summary": f"Research summary for '{query}'",
            "sources": [
                {"title": "Source 1", "url": "https://example.com/1"},
                {"title": "Source 2", "url": "https://example.com/2"}
            ],
            "confidence": 0.85
        }
    
    # Set the handler and activate the agent
    agent.set_execution_handler(execution_handler)
    agent.set_state(AgentState.ACTIVE)
    
    # Register the agent
    registry.register(agent)
    
    print(f"✅ MCP Research Agent created with ID: {agent.agent_id}")
    return agent


# Create a streaming agent
def create_analysis_agent() -> MCPAgent:
    """Create an MCP-compatible analysis agent with streaming support."""
    print("🔍 Creating MCP Analysis Agent with streaming support...")
    
    agent = MCPAgent(
        agent_id="analysis-agent",
        name="Analysis Agent",
        description="Analyzes data and provides insights with real-time updates",
        version="1.0.0",
        capabilities=["analysis", "insights", "trending"],
        accepts_streaming=False,
        produces_streaming=True,
        metadata={
            "creator": "Contexa SDK",
            "specialty": "data analysis"
        }
    )
    
    # Define execution handler
    def execution_handler(content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle non-streaming analysis requests."""
        data = content.get("input_data", {}).get("data", {})
        if not data:
            return {
                "error": "Missing data parameter",
                "code": "missing_parameter"
            }
        
        # Simulate analysis processing
        return {
            "insights": [
                "Key insight 1",
                "Key insight 2",
                "Key insight 3"
            ],
            "metrics": {
                "score": 0.87,
                "confidence": "high",
                "relevance": 0.92
            }
        }
    
    # Define streaming handler
    async def stream_handler(content: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """Handle streaming analysis requests."""
        data = content.get("input_data", {}).get("data", {})
        if not data:
            yield {
                "error": "Missing data parameter",
                "code": "missing_parameter"
            }
            return
        
        # Simulate streaming analysis with multiple updates
        await asyncio.sleep(0.2)
        yield {"status": "starting", "progress": 0.1}
        
        await asyncio.sleep(0.3)
        yield {"status": "processing", "progress": 0.4, "partial_insight": "Initial pattern detected"}
        
        await asyncio.sleep(0.3)
        yield {"status": "processing", "progress": 0.7, "partial_insight": "Secondary correlation found"}
        
        await asyncio.sleep(0.3)
        yield {
            "status": "completed",
            "progress": 1.0,
            "insights": [
                "Key insight 1",
                "Key insight 2",
                "Key insight 3"
            ],
            "metrics": {
                "score": 0.87,
                "confidence": "high",
                "relevance": 0.92
            }
        }
    
    # Set handlers and activate the agent
    agent.set_execution_handler(execution_handler)
    agent.set_stream_handler(stream_handler)
    agent.set_state(AgentState.ACTIVE)
    
    # Register the agent
    registry.register(agent)
    
    print(f"✅ MCP Analysis Agent created with streaming support, ID: {agent.agent_id}")
    return agent


# Create a traditional Contexa agent and adapt it
def create_adapted_reporting_agent() -> ContexaAgent:
    """Create a traditional ContexaAgent and adapt it to MCP."""
    print("📊 Creating traditional Contexa Reporting Agent...")
    
    # Create a standard ContexaAgent
    model = ContexaModel(
        provider="openai",
        model_name="gpt-4-turbo"
    )
    
    report_agent = ContexaAgent(
        name="Report Generator",
        description="Creates formatted reports from structured data",
        model=model,
        tools=[generate_report],
        system_prompt="You are a specialized report generation agent."
    )
    
    # Add an ID to make tracking easier
    report_agent.id = "report-agent"
    
    # Register with the MCP registry
    mcp_agent = register_contexa_agent(report_agent)
    
    print(f"✅ Contexa Report Agent adapted and registered with MCP system")
    return report_agent


async def demonstrate_simple_handoff(research_agent: MCPAgent, analysis_agent: MCPAgent):
    """Demonstrate a simple handoff between two MCP agents."""
    print("\n🔄 Demonstrating simple MCP-to-MCP handoff...")
    
    # Perform a handoff from research agent to analysis agent
    result = handoff(
        source_agent=research_agent,
        target_agent=analysis_agent,
        task_description="Analyze the research findings",
        input_data={
            "data": {
                "research_topic": "quantum computing",
                "findings": [
                    "Key finding 1",
                    "Key finding 2"
                ],
                "sources": 3
            }
        },
        metadata={
            "priority": "high",
            "requestor": "demo_user"
        }
    )
    
    print(f"✅ Handoff completed with status: {result.get('status')}")
    print(f"📋 Result: {json.dumps(result.get('result', {}), indent=2)}")


async def demonstrate_streaming_handoff(research_agent: MCPAgent, analysis_agent: MCPAgent):
    """Demonstrate a streaming handoff between agents."""
    print("\n🔄 Demonstrating streaming handoff response...")
    
    # Perform a streaming handoff
    stream = handoff(
        source_agent=research_agent,
        target_agent=analysis_agent,
        task_description="Analyze the research findings with real-time updates",
        input_data={
            "data": {
                "research_topic": "neural networks",
                "findings": [
                    "Finding A",
                    "Finding B"
                ],
                "sources": 5
            }
        },
        streaming=True  # Enable streaming
    )
    
    # Process the streaming response
    print("📊 Receiving streaming updates:")
    async for chunk in stream:
        status = chunk.get("status")
        if status == "streaming":
            is_last = chunk.get("is_last", False)
            chunk_data = chunk.get("chunk", {})
            
            # Print progress updates
            if "progress" in chunk_data:
                progress = chunk_data.get("progress", 0) * 100
                insight = chunk_data.get("partial_insight", "")
                print(f"  → Progress: {progress:.0f}% - {insight}")
            
            # Print final result
            if is_last:
                print("  → Stream completed")
        elif status == "failed":
            print(f"  → Error: {chunk.get('error')}")


async def demonstrate_mixed_handoff(research_agent: MCPAgent, report_agent: ContexaAgent):
    """Demonstrate handoff between MCP agent and adapted Contexa agent."""
    print("\n🔄 Demonstrating handoff between MCP agent and adapted Contexa agent...")
    
    # Perform a handoff from MCP agent to Contexa agent
    result = handoff(
        source_agent=research_agent,
        target_agent=report_agent,
        task_description="Generate a report from the research findings",
        input_data={
            "title": "Quantum Computing Research",
            "content": {
                "sections": [
                    "Introduction",
                    "Key Findings",
                    "Technical Details",
                    "Future Implications",
                    "Conclusion"
                ]
            }
        }
    )
    
    print(f"✅ Mixed handoff completed with status: {result.get('status')}")
    print(f"📋 Report:\n{result.get('result', {}).get('result', '')}")


async def demonstrate_capability_discovery():
    """Demonstrate capability-based agent discovery."""
    print("\n🔍 Demonstrating capability-based agent discovery...")
    
    # Find agents by capability
    research_capable_agents = registry.find_by_capability("research")
    analysis_capable_agents = registry.find_by_capability("analysis")
    reporting_capable_agents = registry.find_by_capability("report")
    
    print(f"✅ Found {len(research_capable_agents)} agents with research capability")
    print(f"✅ Found {len(analysis_capable_agents)} agents with analysis capability")
    print(f"✅ Found {len(reporting_capable_agents)} agents with reporting capability")
    
    # Display the first agent found for each capability
    if research_capable_agents:
        agent = research_capable_agents[0]
        print(f"  → Research agent: {agent.name} ({agent.agent_id})")
        
    if analysis_capable_agents:
        agent = analysis_capable_agents[0]
        print(f"  → Analysis agent: {agent.name} ({agent.agent_id})")
        
    if reporting_capable_agents:
        agent = reporting_capable_agents[0]
        print(f"  → Reporting agent: {agent.name} ({agent.agent_id})")


async def run_mcp_examples():
    """Run the MCP handoff examples."""
    print("🚀 Demonstrating MCP-Compatible Agent Communication")
    
    # Create our agents
    research_agent = create_research_agent()
    analysis_agent = create_analysis_agent()
    report_agent = create_adapted_reporting_agent()
    
    # Run the demonstrations
    await demonstrate_simple_handoff(research_agent, analysis_agent)
    await demonstrate_streaming_handoff(research_agent, analysis_agent)
    await demonstrate_mixed_handoff(research_agent, report_agent)
    await demonstrate_capability_discovery()
    
    print("\n✅ MCP handoff examples completed")


if __name__ == "__main__":
    asyncio.run(run_mcp_examples()) 