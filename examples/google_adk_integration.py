"""
Example demonstrating Google ADK integration with Contexa SDK.

This example shows how to:
1. Create Contexa tools and convert them to Google ADK tools
2. Create a Contexa agent and convert it to a Google ADK agent
3. Use the Google ADK agent to run tasks
4. Create a multi-agent system with Google ADK
"""

import asyncio
import os
from typing import Dict, List, Any
from pydantic import BaseModel

# Import from Contexa SDK
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent

# Import Google adapter
from contexa_sdk.adapters import google


# Define input classes for tools
class SearchInput(BaseModel):
    query: str


class CalculationInput(BaseModel):
    expression: str


# Define tools
@ContexaTool.register(
    name="web_search",
    description="Search the web for information on a topic"
)
async def web_search(inp: SearchInput) -> str:
    """Search the web for information on a topic."""
    # Simulate a web search API call
    await asyncio.sleep(1)
    return f"Search results for '{inp.query}': Found information about trends, statistics, and analysis."


@ContexaTool.register(
    name="calculator",
    description="Calculate the result of a mathematical expression"
)
async def calculator(inp: CalculationInput) -> str:
    """Calculate the result of a mathematical expression."""
    try:
        # Simple evaluation for demo purposes (not safe for production)
        result = eval(inp.expression)
        return f"Result of {inp.expression} = {result}"
    except Exception as e:
        return f"Error calculating {inp.expression}: {str(e)}"


async def demonstrate_google_adk_integration():
    """Demonstrate Google ADK integration with Contexa SDK."""
    print("🚀 Google ADK Integration Example")
    
    # Create a Contexa model - use new Gemini 2.0 model names
    model = ContexaModel(
        provider="google",
        model_name="gemini-2.0-flash",  # Updated to latest Gemini model
        config={
            "temperature": 0.5,
            # Add API key if needed
            # "api_key": os.environ.get("GOOGLE_API_KEY")
        }
    )
    
    # Create a Contexa agent
    agent = ContexaAgent(
        name="Research Assistant",
        description="A helpful assistant for research and calculations",
        model=model,
        tools=[web_search, calculator],
        system_prompt="You are a Research Assistant that can search for information and perform calculations. Respond in a helpful and concise manner."
    )
    
    # Convert to Google ADK
    try:
        print("\n🔄 Converting Contexa agent to Google ADK agent...")
        adk_agent = await google.agent(agent)
        print("✅ Successfully converted to Google ADK agent")
        
        # Display the ADK agent details
        print(f"\nℹ️ ADK Agent Details:")
        print(f"  - Name: {adk_agent.name}")
        print(f"  - Model: {adk_agent.model}")
        print(f"  - Tools: {[getattr(t, 'name', t.__name__) for t in adk_agent.tools]}")
        
        # Run the Google ADK agent
        print("\n🤖 Running Google ADK agent...")
        
        # In ADK, you would typically run the agent like this:
        print("📊 Query: What is the capital of France and what is 15 * 24?")
        
        # For demonstration purposes, we'll show the ADK usage pattern
        print("""
If Google ADK is properly installed, you would run:

from google.adk.web import web
web([adk_agent])  # Launch the ADK UI

# Or run the agent directly
response = await adk_agent.run("What is the capital of France and what is 15 * 24?")
print(f"Response: {response}")
        """)
        
        # Convert back to Contexa
        print("\n🔄 Converting Google ADK agent back to Contexa agent...")
        contexa_agent = await google.adapt_agent(adk_agent)
        print("✅ Successfully converted back to Contexa agent")
        
        # Run the converted agent using Contexa's interface
        print("\n🤖 Running converted agent through Contexa...")
        response = await contexa_agent.run("What is the capital of France and what is 15 * 24?")
        print(f"🔍 Response: {response}")
        
    except ImportError:
        print("❌ Google ADK not installed. Install with `pip install google-adk`")
        print("📝 Reference: https://github.com/google/adk-python")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n🔗 Demonstrating Google ADK multi-agent system")
    try:
        # Create multiple specialized agents
        search_agent = ContexaAgent(
            name="Search Specialist",
            description="An agent specialized in web search",
            model=model,
            tools=[web_search],
            system_prompt="You are a search specialist that provides accurate information from the web."
        )
        
        calc_agent = ContexaAgent(
            name="Calculation Specialist",
            description="An agent specialized in calculations",
            model=model,
            tools=[calculator],
            system_prompt="You are a calculation specialist that performs accurate mathematical calculations."
        )
        
        # Convert to Google ADK agents
        adk_search_agent = await google.agent(search_agent)
        adk_calc_agent = await google.agent(calc_agent)
        
        # In ADK, you would create a multi-agent system like this:
        print("""
If Google ADK is properly installed, you would create a multi-agent system like:

from google.adk.agents import LlmAgent

# Create coordinator agent with sub-agents
coordinator = LlmAgent(
    name="Coordinator",
    model="gemini-2.0-flash",
    description="I coordinate search and calculation tasks.",
    sub_agents=[adk_search_agent, adk_calc_agent]
)

# Run the coordinator agent
response = await coordinator.run("I need to search for Paris population and calculate its growth rate.")
        """)
        
        print("\n✅ Successfully demonstrated Google ADK multi-agent pattern")
        
    except ImportError:
        print("❌ Google ADK not installed. Install with `pip install google-adk`")
        print("📝 Reference: https://github.com/google/adk-python")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n✅ Google ADK integration example completed")


if __name__ == "__main__":
    asyncio.run(demonstrate_google_adk_integration()) 