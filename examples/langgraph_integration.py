"""
Example demonstrating LangGraph workflow integration with Contexa SDK.

This example shows how to:
1. Create a Contexa AgentTeam with multiple specialized agents
2. Convert the team to a LangGraph workflow
3. Execute the workflow to accomplish a multi-step task

This integration allows you to use Contexa's agent definitions with LangGraph's
powerful workflow orchestration capabilities.
"""

import asyncio
from typing import Dict, List, Any
from pydantic import BaseModel

# Import from Contexa SDK
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.orchestration import AgentTeam, TaskHandoff

# Import LangChain adapter with LangGraph support
from contexa_sdk.adapters import langchain


# Define input classes for tools
class SearchInput(BaseModel):
    query: str


class AnalysisInput(BaseModel):
    data: str


class WriteInput(BaseModel):
    topic: str
    length: int = 100


# Define tools
@ContexaTool.register(
    name="web_search",
    description="Search the web for information on a topic"
)
async def web_search(inp: SearchInput) -> str:
    """Search the web for information on a topic."""
    # Simulate a web search API call
    await asyncio.sleep(1)
    return f"Search results for '{inp.query}': Found information about key concepts, history, and applications."


@ContexaTool.register(
    name="analyze_data",
    description="Analyze data and extract insights"
)
async def analyze_data(inp: AnalysisInput) -> str:
    """Analyze data and extract insights."""
    # Simulate data analysis
    await asyncio.sleep(1)
    return f"Analysis of data: Found several key insights including trends and patterns."


@ContexaTool.register(
    name="write_content",
    description="Write content on a specified topic"
)
async def write_content(inp: WriteInput) -> str:
    """Write content on a specified topic."""
    # Simulate content writing
    await asyncio.sleep(1)
    return f"Generated {inp.length} words of content about {inp.topic}."


async def demonstrate_langgraph_integration():
    """Demonstrate LangGraph workflow integration with Contexa SDK."""
    print("🔄 LangGraph Workflow Integration Example")
    
    # Create specialized agents
    research_agent = ContexaAgent(
        name="Researcher",
        description="Specialized in finding information from the web",
        model=ContexaModel(provider="openai", model_name="gpt-4o"),
        tools=[web_search],
        system_prompt="You are a research specialist who finds detailed information. Hand off analysis tasks to the Analyst."
    )
    
    analysis_agent = ContexaAgent(
        name="Analyst",
        description="Specialized in analyzing data and extracting insights",
        model=ContexaModel(provider="openai", model_name="gpt-4o"),
        tools=[analyze_data],
        system_prompt="You are an analyst who excels at interpreting data. Hand off writing tasks to the Writer."
    )
    
    writing_agent = ContexaAgent(
        name="Writer",
        description="Specialized in creating compelling content",
        model=ContexaModel(provider="openai", model_name="gpt-4o"),
        tools=[write_content],
        system_prompt="You are a content writer who creates engaging articles based on research and analysis."
    )
    
    # Create an AgentTeam
    team = AgentTeam(
        name="Content Creation Team",
        description="A team that researches, analyzes, and writes content"
    )
    
    # Add agents with roles
    team.add_agent(research_agent, role="lead")
    team.add_agent(analysis_agent, role="specialist")
    team.add_agent(writing_agent, role="specialist")
    
    # Define task handoffs
    research_to_analysis = TaskHandoff(
        sender=research_agent,
        recipient=analysis_agent,
        task_description="Analyze the research findings"
    )
    
    analysis_to_writing = TaskHandoff(
        sender=analysis_agent,
        recipient=writing_agent,
        task_description="Write content based on the analysis"
    )
    
    # Add handoffs to the team
    team.add_handoff(research_to_analysis)
    team.add_handoff(analysis_to_writing)
    
    # Try to convert to LangGraph workflow
    try:
        # Check if LangGraph support is available
        if not hasattr(langchain, "orchestration_to_langgraph"):
            print("❌ LangGraph support not available. Install with `pip install langgraph`")
            return
            
        print("\n🔄 Converting Contexa AgentTeam to LangGraph workflow...")
        workflow = langchain.orchestration_to_langgraph(team)
        print("✅ Successfully converted to LangGraph workflow")
        
        # Running the workflow
        print("\n🤖 Running the LangGraph workflow...")
        print("📝 Input: Research artificial intelligence and write a blog post")
        
        # In a real implementation, you would run the workflow like this:
        print("""
If LangGraph is properly installed, you would run:

# Set initial state
initial_state = {
    "messages": [{"role": "user", "content": "Research artificial intelligence and write a blog post"}],
    "current_agent": None,
    "agents": {},
    "artifacts": {}
}

# Execute the compiled graph
result = workflow.invoke(initial_state)
print(f"Final result: {result}")
        """)
        
        print("\n✅ LangGraph integration example completed")
        
    except ImportError:
        print("❌ LangGraph not installed. Install with `pip install langgraph`")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(demonstrate_langgraph_integration()) 