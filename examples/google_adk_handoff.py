"""Example demonstrating handoffs between Google ADK agents.

This example shows how to:
1. Create Contexa agents with Google models
2. Convert them to Google ADK agents
3. Perform a handoff between agents to complete a multi-step task

The handoff allows agents to collaborate by transferring context and tasks
between each other.
"""

import asyncio
from typing import Dict, Any
from pydantic import BaseModel

# Import from Contexa SDK
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent

# Import Google ADK adapter with handoff support
from contexa_sdk.adapters import google


# Define input classes for tools
class SearchInput(BaseModel):
    query: str


class WritingInput(BaseModel):
    topic: str
    key_points: str


# Define tools for the agents
@ContexaTool.register(
    name="search_tool",
    description="Search for information on a given topic"
)
async def search_tool(inp: SearchInput) -> str:
    """Search for information on a given topic."""
    # Simulate a search
    await asyncio.sleep(1)
    return f"Search results for {inp.query}: Found information about context, history, and impacts."


@ContexaTool.register(
    name="write_content",
    description="Write content based on a topic and key points"
)
async def write_content(inp: WritingInput) -> str:
    """Write content based on a topic and key points."""
    # Simulate content writing
    await asyncio.sleep(1)
    return f"Generated content about {inp.topic} covering key points: {inp.key_points}"


async def demonstrate_google_adk_handoff():
    """Demonstrate handoffs between Google ADK agents."""
    print("🔄 Google ADK Handoff Example")
    
    # Create Contexa research agent
    research_agent = ContexaAgent(
        name="Research Agent",
        description="An agent that searches for information",
        model=ContexaModel(
            provider="google",
            model_name="gemini-pro",
            config={"temperature": 0.5}
        ),
        tools=[search_tool],
        system_prompt="You are a research agent that finds information on topics. When you find information, hand it off to the content writer."
    )
    
    # Create Contexa writing agent
    writing_agent = ContexaAgent(
        name="Content Writer",
        description="An agent that writes content based on research",
        model=ContexaModel(
            provider="google", 
            model_name="gemini-pro",
            config={"temperature": 0.7}
        ),
        tools=[write_content],
        system_prompt="You are a content writing agent that creates high-quality content based on research. You expect to receive research information in the context."
    )
    
    try:
        # Convert to Google ADK agents
        print("\n🔄 Converting agents to Google ADK format...")
        research_adk_agent = await google.convert_agent(research_agent)
        writing_adk_agent = await google.convert_agent(writing_agent)
        print("✅ Successfully converted agents to Google ADK")
        
        # Initial query for the research agent
        query = "What are the key components of artificial intelligence?"
        
        try:
            # Run the research agent
            print(f"\n🔍 Running research agent with query: '{query}'")
            research_result = await research_adk_agent.run(query)
            print(f"📊 Research Result: {research_result}")
            
            # Prepare handoff to the writing agent
            print("\n🔄 Handing off to the writing agent...")
            handoff_query = "Write a short introduction to artificial intelligence based on the research"
            handoff_context = {"research_findings": research_result}
            
            # Perform the handoff
            writing_result = await google.handoff(
                source_agent=research_agent,
                target_adk_agent=writing_adk_agent,
                query=handoff_query,
                context=handoff_context
            )
            
            print(f"\n📝 Writing Result: {writing_result}")
            
            # Check the research agent's memory for the handoff
            print("\n🧠 Checking handoff record in research agent's memory...")
            for handoff in research_agent.memory.handoffs:
                print(f"  - Handoff to: {handoff.recipient_name}")
                print(f"  - Task: {handoff.query}")
                print(f"  - Result: {handoff.result[:100]}...")
                
        except Exception as e:
            print(f"❌ Error during agent execution: {str(e)}")
            
    except ImportError:
        print("❌ Google ADK not installed. Install with `pip install google-adk`")
        print("📝 Reference: https://github.com/google/adk-python")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n✅ Google ADK handoff example completed")


if __name__ == "__main__":
    asyncio.run(demonstrate_google_adk_handoff()) 