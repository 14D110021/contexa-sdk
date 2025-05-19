"""
Google Adapter Comparison Example

This example demonstrates the key differences between the Google GenAI and Google ADK adapters,
showing when to use each one based on your specific requirements.

Requirements:
- For GenAI: pip install google-generativeai
- For ADK: pip install google-adk
"""

import asyncio
import os
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.adapters.google import genai_agent, adk_agent

# Optional: Set your API key here if not using environment variables
# os.environ["GOOGLE_API_KEY"] = "your-api-key-here"

# --------- DEFINE TOOLS ---------

@ContexaTool.register(
    name="weather",
    description="Get the current weather for a location"
)
async def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    # In a real implementation, this would call a weather API
    return f"It's currently sunny and 72°F in {location}."

@ContexaTool.register(
    name="search",
    description="Search for information on the web"
)
async def search(query: str) -> str:
    """Search for information on the web."""
    # In a real implementation, this would perform a web search
    return f"Search results for '{query}': (1) Top result, (2) Second result, (3) Third result"

@ContexaTool.register(
    name="complex_analysis",
    description="Perform complex data analysis requiring multi-step reasoning"
)
async def complex_analysis(data: str, analysis_type: str = "standard") -> str:
    """Perform complex multi-step analysis."""
    # Simulate a complex analysis task
    return f"Completed {analysis_type} analysis on data: {data[:30]}... [Analysis results]"

# --------- CREATE BASE AGENT ---------

# Create a Contexa agent that we'll convert to both adapter types
base_agent = ContexaAgent(
    name="Multi-purpose Assistant",
    description="A helpful assistant that can answer questions and perform tasks",
    model=ContexaModel(
        provider="google",
        model_name="gemini-pro",  # This gets mapped appropriately in each adapter
    ),
    tools=[get_weather, search, complex_analysis],
    system_prompt="You are a helpful AI assistant. Use the provided tools to answer questions."
)

# --------- ADAPTER COMPARISON ---------

async def main():
    print("\n===== GOOGLE ADAPTER COMPARISON =====\n")
    
    # Create agents using both adapters
    genai_assistant = genai_agent(base_agent)
    adk_assistant = adk_agent(base_agent)
    
    # Example queries to demonstrate differences
    simple_query = "What's the weather in San Francisco?"
    web_search_query = "Find information about climate change"
    complex_query = "Analyze the GDP trends for the top 5 economies and explain their correlation with technological innovation"
    
    # ----- WHEN TO USE GOOGLE GENAI ADAPTER -----
    print("========== GOOGLE GENAI ADAPTER ==========")
    print("Best for: Simple interactions, standard tool usage, direct model access")
    print("Advantages: Simpler integration, direct access to Gemini models, faster setup\n")
    
    print(f"Query: {simple_query}")
    try:
        response = await genai_assistant.run(simple_query)
        print(f"Response: {response}\n")
    except Exception as e:
        print(f"Error: {str(e)}\n")
        
    print(f"Query: {web_search_query}")
    try:
        response = await genai_assistant.run(web_search_query)
        print(f"Response: {response}\n")
    except Exception as e:
        print(f"Error: {str(e)}\n")
    
    # ----- WHEN TO USE GOOGLE ADK ADAPTER -----
    print("\n========== GOOGLE ADK ADAPTER ==========")
    print("Best for: Complex scenarios, multi-step reasoning, advanced agent capabilities")
    print("Advantages: Better with complex reasoning, advanced agent features, multi-agent systems\n")
    
    print(f"Query: {complex_query}")
    try:
        response = await adk_assistant.run(complex_query)
        print(f"Response: {response}\n")
    except Exception as e:
        print(f"Error: {str(e)}\n")
    
    # ----- COMPARISON SUMMARY -----
    print("\n===== WHEN TO USE EACH ADAPTER =====")
    print("\nUse Google GenAI Adapter when:")
    print("- You need simple, direct access to Gemini models")
    print("- Your tasks involve straightforward tool usage")
    print("- You want minimum setup and dependencies")
    print("- Performance and simplicity are priorities")
    
    print("\nUse Google ADK Adapter when:")
    print("- You need advanced agent capabilities")
    print("- Your tasks involve complex, multi-step reasoning")
    print("- You're building multi-agent systems")
    print("- You need ADK-specific features like agent evaluation tools")
    print("- Your application benefits from Google's agent development ecosystem")

if __name__ == "__main__":
    asyncio.run(main()) 