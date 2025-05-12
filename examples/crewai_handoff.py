"""Example demonstrating handoffs between Contexa and CrewAI agents.

This example shows how to:
1. Create Contexa agents
2. Convert them to CrewAI agents/crews
3. Perform a handoff from a Contexa agent to a CrewAI crew
4. Observe how context is preserved during the handoff
"""

import asyncio
from typing import Dict, List, Any
from pydantic import BaseModel

# Import from Contexa SDK
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent

# Import CrewAI adapter with handoff support
from contexa_sdk.adapters import crewai


# Define input classes for tools
class ResearchInput(BaseModel):
    topic: str


class WriteReportInput(BaseModel):
    research: str
    style: str = "professional"


# Define research tool
@ContexaTool.register(
    name="research_tool",
    description="Conduct in-depth research on a topic"
)
async def research_tool(inp: ResearchInput) -> str:
    """Conduct research on a given topic."""
    # Simulate research process
    await asyncio.sleep(1)
    
    if "climate" in inp.topic.lower():
        return (
            "Research findings on climate change:\n"
            "1. Global temperatures have risen by about 1.1°C since pre-industrial times\n"
            "2. Sea levels are rising at an accelerated rate\n"
            "3. Extreme weather events are becoming more frequent\n"
            "4. Carbon dioxide levels are at their highest in 800,000 years\n"
            "5. Various mitigation strategies are being developed worldwide"
        )
    elif "ai" in inp.topic.lower():
        return (
            "Research findings on artificial intelligence:\n"
            "1. Machine learning models are growing exponentially in size\n"
            "2. Foundation models have revolutionized the field since 2018\n"
            "3. Major concerns include bias, hallucinations, and safety\n"
            "4. AI is being applied across industries from healthcare to finance\n"
            "5. Regulatory frameworks are being developed globally"
        )
    else:
        return f"Research findings on {inp.topic}: Found key information on history, current state, and future trends."


# Define report writing tool
@ContexaTool.register(
    name="write_report",
    description="Write a professional report based on research"
)
async def write_report(inp: WriteReportInput) -> str:
    """Write a report based on research."""
    # Simulate report writing
    await asyncio.sleep(1)
    
    style_prefix = "Detailed" if inp.style == "professional" else "Simplified"
    return f"{style_prefix} report based on the following research:\n\n{inp.research}\n\nThe report includes an executive summary, key findings, analysis, and recommendations."


async def demonstrate_crewai_handoff():
    """Demonstrate handoffs between Contexa and CrewAI agents."""
    print("🤝 CrewAI Handoff Example")
    
    # Create a Contexa researcher agent
    researcher = ContexaAgent(
        name="Research Specialist",
        description="Expert at conducting thorough research on any topic",
        model=ContexaModel(provider="openai", model_name="gpt-4"),
        tools=[research_tool],
        system_prompt="You are a research specialist who digs deep into topics to find comprehensive information."
    )
    
    # Create a Contexa report writer agent
    report_writer = ContexaAgent(
        name="Report Writer",
        description="Expert at writing professional reports based on research",
        model=ContexaModel(provider="openai", model_name="gpt-4"),
        tools=[write_report],
        system_prompt="You are a professional report writer who creates well-structured, insightful reports based on research findings."
    )
    
    try:
        # Convert the report writer to a CrewAI crew
        print("\n🔄 Converting report writer to CrewAI crew...")
        crew_report_writer = crewai.agent(report_writer)
        print("✅ Successfully converted to CrewAI crew")
        
        # Run the researcher agent with a query
        print("\n🔍 Running researcher with query: 'Research the impacts of climate change'")
        research_result = await researcher.run("Research the impacts of climate change")
        print(f"\n📊 Research Result:\n{research_result}")
        
        # Perform a handoff from the Contexa researcher to the CrewAI report writer
        print("\n🤝 Handing off from Contexa researcher to CrewAI report writer...")
        handoff_query = "Write a detailed report on climate change impacts based on the research"
        handoff_context = {
            "research_data": research_result,
            "report_style": "professional",
            "audience": "policymakers"
        }
        
        # Execute the handoff
        report = await crewai.handoff(
            source_agent=researcher,
            target_crew=crew_report_writer,
            query=handoff_query,
            context=handoff_context
        )
        
        print(f"\n📝 Final Report:\n{report}")
        
        # Check the researcher's memory for the handoff record
        print("\n🧠 Checking handoff record in researcher's memory...")
        for handoff in researcher.memory.handoffs:
            print(f"  - Handoff to: {handoff.recipient_name}")
            print(f"  - Task: {handoff.query}")
            print(f"  - Result received: {'Yes' if handoff.result else 'No'}")
        
    except ImportError:
        print("❌ CrewAI not installed. Install with `pip install crewai`")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n✅ CrewAI handoff example completed")


if __name__ == "__main__":
    asyncio.run(demonstrate_crewai_handoff()) 