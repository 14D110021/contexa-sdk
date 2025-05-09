"""Example demonstrating multi-framework integration with Contexa SDK.

This example shows how to connect agents from different frameworks:
1. A LangChain agent that handles web research
2. A CrewAI agent that handles analysis
3. An OpenAI function-calling agent that handles response generation
4. A Google Vertex AI agent for final summarization

The agents work together to complete a complex task while preserving context
across framework boundaries.
"""

import asyncio
import os
from typing import Dict, List, Any
from pydantic import BaseModel

# Import from Contexa SDK
from contexa_sdk.core.tool import BaseTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent, HandoffData
from contexa_sdk.client import tools, models, agents

# Import framework adapters
from contexa_sdk.adapters.langchain import convert_agent_to_langchain, adapt_langchain_agent
from contexa_sdk.adapters.crewai import convert_agent_to_crewai, adapt_crewai_agent
from contexa_sdk.adapters.openai import convert_agent_to_openai, adapt_openai_assistant
from contexa_sdk.adapters.google import convert_agent_to_google, adapt_google_agent


# Define input classes for tools
class SearchInput(BaseModel):
    query: str


class AnalysisInput(BaseModel):
    data: str
    focus: str


class GenerationInput(BaseModel):
    context: str
    target_audience: str
    tone: str


class SummaryInput(BaseModel):
    content: str
    max_length: int = 100


# Register tools
@tools.register("web_search")
async def web_search(query: str) -> Dict[str, Any]:
    """Search the web for information on a topic."""
    # Simulate a web search API call
    await asyncio.sleep(1)
    return {
        "result": f"Search results for '{query}': Found information about trends, statistics, and market analysis."
    }


@tools.register("analyze_data")
async def analyze_data(data: str, focus: str) -> Dict[str, Any]:
    """Analyze data with a specific focus."""
    # Simulate data analysis
    await asyncio.sleep(1)
    return {
        "result": f"Analysis of data focusing on '{focus}': The data shows significant patterns related to {focus}."
    }


@tools.register("generate_content")
async def generate_content(context: str, target_audience: str, tone: str) -> Dict[str, Any]:
    """Generate content based on context for a specific audience and tone."""
    # Simulate content generation
    await asyncio.sleep(1)
    return {
        "result": f"Generated {tone} content for {target_audience} based on the provided context."
    }


@tools.register("summarize")
async def summarize(content: str, max_length: int = 100) -> Dict[str, Any]:
    """Summarize content to the specified maximum length."""
    # Simulate summarization
    await asyncio.sleep(1)
    return {
        "result": f"Summary (max {max_length} words): Key points from the content have been condensed."
    }


async def demonstrate_multi_framework_integration():
    """Demonstrate how to integrate agents from multiple frameworks."""
    print("🔗 Demonstration of multi-framework integration with Contexa SDK")
    
    # Register models with the registry
    gpt4 = models.register(
        "gpt-4",
        ContexaModel(model_name="gpt-4", provider="openai", temperature=0.7)
    )
    
    palm = models.register(
        "gemini-pro",
        ContexaModel(model_name="gemini-pro", provider="google", temperature=0.3)
    )
    
    # Create specialized agents
    
    # 1. Research agent (will be converted to LangChain)
    research_agent = agents.register(
        "research_agent",
        ContexaAgent(
            name="Research Agent",
            description="Searches the web for information",
            tools=[tools.get("web_search")],
            model=models.get("gpt-4"),
            system_prompt="You are a research assistant specialized in finding information on the web.",
        )
    )
    
    # 2. Analysis agent (will be converted to CrewAI)
    analysis_agent = agents.register(
        "analysis_agent",
        ContexaAgent(
            name="Analysis Agent",
            description="Analyzes data and extracts insights",
            tools=[tools.get("analyze_data")],
            model=models.get("gpt-4"),
            system_prompt="You are a data analyst specialized in identifying patterns and insights.",
        )
    )
    
    # 3. Generation agent (will be converted to OpenAI Assistant)
    generation_agent = agents.register(
        "generation_agent",
        ContexaAgent(
            name="Generation Agent",
            description="Generates content based on analysis",
            tools=[tools.get("generate_content")],
            model=models.get("gpt-4"),
            system_prompt="You are a content generator specialized in creating engaging material.",
        )
    )
    
    # 4. Summary agent (will be converted to Google AI)
    summary_agent = agents.register(
        "summary_agent",
        ContexaAgent(
            name="Summary Agent",
            description="Summarizes content concisely",
            tools=[tools.get("summarize")],
            model=models.get("gemini-pro"),
            system_prompt="You are a summarization specialist that condenses information effectively.",
        )
    )
    
    # Convert agents to different frameworks
    
    # Convert and adapt LangChain
    try:
        print("\n🔄 Converting Research Agent to LangChain...")
        langchain_agent = await convert_agent_to_langchain(research_agent)
        print("✅ Successfully converted to LangChain agent")
        
        # Convert LangChain agent back to Contexa
        print("\n🔄 Adapting LangChain agent back to Contexa...")
        contexa_langchain_agent = await adapt_langchain_agent(langchain_agent)
        print("✅ Successfully adapted LangChain agent to Contexa")
        
    except ImportError:
        print("❌ LangChain not installed, using original Contexa agent instead")
        contexa_langchain_agent = research_agent
    
    # Convert and adapt CrewAI
    try:
        print("\n🔄 Converting Analysis Agent to CrewAI...")
        crewai_agent = await convert_agent_to_crewai(analysis_agent)
        print("✅ Successfully converted to CrewAI agent")
        
        # Convert CrewAI agent back to Contexa
        print("\n🔄 Adapting CrewAI agent back to Contexa...")
        contexa_crewai_agent = await adapt_crewai_agent(crewai_agent)
        print("✅ Successfully adapted CrewAI agent to Contexa")
        
    except ImportError:
        print("❌ CrewAI not installed, using original Contexa agent instead")
        contexa_crewai_agent = analysis_agent
    
    # Convert and adapt OpenAI
    try:
        print("\n🔄 Converting Generation Agent to OpenAI...")
        openai_agent = await convert_agent_to_openai(generation_agent)
        print("✅ Successfully converted to OpenAI agent")
        
        # In a real scenario, we would use a real OpenAI Assistant ID
        # Since we don't have one, we're using the original agent
        print("\n⚠️ Skipping OpenAI assistant adaptation (would need real Assistant ID)")
        contexa_openai_agent = generation_agent
        
    except ImportError:
        print("❌ OpenAI not installed, using original Contexa agent instead")
        contexa_openai_agent = generation_agent
    
    # Convert and adapt Google
    try:
        print("\n🔄 Converting Summary Agent to Google AI...")
        google_agent = await convert_agent_to_google(summary_agent)
        print("✅ Successfully converted to Google AI agent")
        
        # Convert Google agent back to Contexa
        print("\n🔄 Adapting Google AI agent back to Contexa...")
        contexa_google_agent = await adapt_google_agent(google_agent)
        print("✅ Successfully adapted Google AI agent to Contexa")
        
    except ImportError:
        print("❌ Google AI not installed, using original Contexa agent instead")
        contexa_google_agent = summary_agent
    
    # Demonstrate the end-to-end workflow with agent handoffs
    print("\n🔄 Starting multi-framework workflow with agent handoffs...")
    
    # Initial task for the research agent
    initial_query = "Research the latest trends in artificial intelligence for business applications"
    print(f"\n📝 Initial Query: {initial_query}")
    
    # 1. Research agent (LangChain) finds information
    print("\n🤖 Research Agent (LangChain) is searching...")
    research_result = await contexa_langchain_agent.run(initial_query)
    print(f"📊 Research Result: {research_result}")
    
    # 2. Hand off to analysis agent (CrewAI)
    print("\n🔄 Handing off to Analysis Agent (CrewAI)...")
    analysis_query = f"Analyze this data with focus on ROI: {research_result}"
    analysis_result = await contexa_crewai_agent.run(analysis_query)
    print(f"📈 Analysis Result: {analysis_result}")
    
    # 3. Hand off to generation agent (OpenAI)
    print("\n🔄 Handing off to Generation Agent (OpenAI)...")
    generation_query = f"Generate content for business executives with a professional tone based on: {analysis_result}"
    generation_result = await contexa_openai_agent.run(generation_query)
    print(f"📝 Generated Content: {generation_result}")
    
    # 4. Hand off to summary agent (Google AI)
    print("\n🔄 Handing off to Summary Agent (Google AI)...")
    summary_query = f"Summarize in 50 words: {generation_result}"
    summary_result = await contexa_google_agent.run(summary_query)
    print(f"📋 Final Summary: {summary_result}")
    
    print("\n✅ Multi-framework workflow completed successfully")
    
    # Demonstrate direct handoffs between native Contexa agents
    print("\n🔄 Demonstrating direct handoffs between native Contexa agents...")
    
    # Direct handoff using the handoff_to method
    result = await research_agent.run("What are the latest trends in renewable energy?")
    print(f"📊 Initial Research: {result}")
    
    # Hand off to analysis agent with history
    handoff_data = HandoffData(
        target_agent_id=analysis_agent.agent_id,
        query="Analyze this research data with focus on costs and benefits",
        conversation_history=[
            {"role": "user", "content": "What are the latest trends in renewable energy?"},
            {"role": "assistant", "content": result}
        ]
    )
    
    # Perform the handoff
    analysis_result = await research_agent.handoff_to(handoff_data)
    print(f"📈 Handoff Analysis: {analysis_result}")
    
    print("\n✅ Direct handoff demonstration completed successfully")


if __name__ == "__main__":
    asyncio.run(demonstrate_multi_framework_integration()) 