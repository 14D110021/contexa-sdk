"""Example demonstrating CrewAI orchestration integration with Contexa SDK.

This example shows how to:
1. Create a Contexa AgentTeam with multiple specialized agents and defined handoffs
2. Convert the team to a CrewAI Crew for execution
3. Execute the Crew to accomplish a multi-step task

This integration allows leveraging CrewAI's native workflow capabilities with
Contexa's standardized agent definitions.
"""

import asyncio
from typing import Dict, List, Any
from pydantic import BaseModel

# Import from Contexa SDK
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.orchestration import AgentTeam, TaskHandoff

# Import CrewAI adapter with orchestration support
from contexa_sdk.adapters import crewai


# Define input classes for tools
class ResearchInput(BaseModel):
    query: str


class AnalysisInput(BaseModel):
    data: str


class WritingInput(BaseModel):
    analysis: str
    audience: str = "general"


# Define tools
@ContexaTool.register(
    name="research_tool",
    description="Research a topic and gather information"
)
async def research_tool(inp: ResearchInput) -> str:
    """Research a topic and gather information."""
    # Simulate research process
    await asyncio.sleep(1)
    
    if "renewable" in inp.query.lower():
        return (
            "Research on renewable energy:\n"
            "- Solar energy capacity grew by 22% globally last year\n"
            "- Wind energy costs have decreased by 40% in the past decade\n"
            "- Battery storage technologies have improved efficiency by 35%\n"
            "- Global investment in renewables reached $500B in 2022\n"
            "- Transition to renewables could create 30M jobs by 2030"
        )
    else:
        return f"Research findings on {inp.query}: Found key statistics, trends, and insights."


@ContexaTool.register(
    name="analyze_data",
    description="Analyze data and extract insights"
)
async def analyze_data(inp: AnalysisInput) -> str:
    """Analyze data and extract insights."""
    # Simulate analysis process
    await asyncio.sleep(1)
    return f"Analysis of data:\n\nThe provided information indicates several key insights:\n1. Rapid growth trends\n2. Cost reductions making technologies more accessible\n3. Potential for significant job creation\n4. Strong investment signals\n5. Technical improvements driving adoption"


@ContexaTool.register(
    name="write_content",
    description="Write content based on analysis"
)
async def write_content(inp: WritingInput) -> str:
    """Write content based on analysis."""
    # Simulate writing process
    await asyncio.sleep(1)
    
    audience_prefix = "Technical" if inp.audience == "technical" else "General audience"
    return f"{audience_prefix} content based on analysis:\n\n{inp.analysis}\n\nThe content connects these insights into a cohesive narrative with clear implications and recommendations."


async def demonstrate_crewai_orchestration():
    """Demonstrate CrewAI orchestration integration with Contexa SDK."""
    print("🔄 CrewAI Orchestration Integration Example")
    
    # Create specialized agents for different roles
    researcher = ContexaAgent(
        name="Researcher",
        description="Specialized in gathering comprehensive information",
        model=ContexaModel(provider="openai", model_name="gpt-4"),
        tools=[research_tool],
        system_prompt="You are a research specialist who gathers thorough information on topics. After completing research, hand off to the Analyst."
    )
    
    analyst = ContexaAgent(
        name="Analyst",
        description="Specialized in analyzing data and extracting insights",
        model=ContexaModel(provider="openai", model_name="gpt-4"),
        tools=[analyze_data],
        system_prompt="You are a data analyst who extracts meaningful insights from research. After completing analysis, hand off to the Writer."
    )
    
    writer = ContexaAgent(
        name="Writer",
        description="Specialized in creating compelling content",
        model=ContexaModel(provider="openai", model_name="gpt-4"),
        tools=[write_content],
        system_prompt="You are a content writer who creates engaging, well-structured content based on analysis."
    )
    
    # Create an AgentTeam with these agents
    team = AgentTeam(
        name="Content Creation Team",
        description="A team that researches, analyzes, and creates content on renewable energy"
    )
    
    # Add agents with defined roles
    team.add_agent(researcher, role="lead")
    team.add_agent(analyst, role="specialist")
    team.add_agent(writer, role="specialist")
    
    # Define explicit handoffs between agents
    research_to_analysis = TaskHandoff(
        sender=researcher,
        recipient=analyst,
        task_description="Analyze the research findings on renewable energy"
    )
    
    analysis_to_writing = TaskHandoff(
        sender=analyst,
        recipient=writer,
        task_description="Create content based on the analysis of renewable energy research"
    )
    
    # Add handoffs to the team
    team.add_handoff(research_to_analysis)
    team.add_handoff(analysis_to_writing)
    
    try:
        # Check if orchestration support is available
        if not hasattr(crewai, "agent_team_to_crew"):
            print("❌ CrewAI orchestration support not available.")
            return
            
        # Convert the Contexa AgentTeam to a CrewAI Crew
        print("\n🔄 Converting Contexa AgentTeam to CrewAI Crew...")
        
        crew = crewai.agent_team_to_crew(team)
        print(f"✅ Successfully converted to CrewAI Crew with {len(crew.agents)} agents and {len(crew.tasks)} tasks")
        
        # Display the crew configuration
        print("\n👥 CrewAI Crew Configuration:")
        print(f"  Agents:")
        for crew_agent in crew.agents:
            print(f"  - {crew_agent.role}: {crew_agent.goal}")
        
        print(f"  Tasks:")
        for task in crew.tasks:
            print(f"  - {task.description} (assigned to {task.agent.role})")
        
        # In CrewAI, you would run the crew like this
        print("\n🤖 Running the CrewAI crew...")
        print("""
If CrewAI is properly installed, you would run:

# The CrewAI execution
result = crew.kickoff(inputs={
    "topic": "renewable energy trends in 2023"
})
print(f"Final result: {result}")
        """)
        
        # Convert back to Contexa
        print("\n🔄 Converting CrewAI Crew back to Contexa AgentTeam...")
        converted_team = await crewai.adapt_crew_to_agent_team(crew)
        print(f"✅ Successfully converted back to Contexa AgentTeam with {len(converted_team.agents)} agents")
        
    except ImportError:
        print("❌ CrewAI not installed. Install with `pip install crewai`")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n✅ CrewAI orchestration example completed")


if __name__ == "__main__":
    asyncio.run(demonstrate_crewai_orchestration()) 