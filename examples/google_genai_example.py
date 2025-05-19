"""
Example of using the Google GenAI adapter in Contexa SDK.

This example demonstrates how to use Google's Generative AI SDK (Gemini)
with Contexa SDK's adapter system.

Requirements:
- google-generativeai package: pip install google-generativeai
"""

import asyncio
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.adapters.google import genai_model, genai_tool, genai_agent


# Define a simple tool
class WebSearchInput:
    query: str
    
@ContexaTool.register(
    name="web_search",
    description="Search the web for information on a given query"
)
async def web_search(query: str) -> str:
    """Simulate a web search (in a real app, you would implement an actual search)."""
    results = {
        "climate change": "Climate change refers to long-term shifts in temperatures and weather patterns.",
        "artificial intelligence": "AI is the simulation of human intelligence by machines.",
        "quantum computing": "Quantum computing uses quantum mechanics to perform computations.",
    }
    
    return results.get(query.lower(), f"No specific information found for '{query}'. Try another query.")


async def main():
    # Create a Contexa model for Google's Gemini
    model = ContexaModel(
        provider="google",
        model_name="gemini-pro",  # Use your preferred Gemini model
        config={
            # Uncomment and add your API key if not using environment variables
            # "api_key": "YOUR_API_KEY_HERE"
        }
    )
    
    # Create a Contexa agent with the model and tool
    agent = ContexaAgent(
        name="Research Assistant",
        description="A helpful assistant that can search the web for information",
        model=model,
        tools=[web_search],
        system_prompt="You are a helpful research assistant. Use the provided tools to answer user questions."
    )
    
    # Convert the agent to a Google GenAI agent
    google_agent = genai_agent(agent)
    
    # Example queries to run
    queries = [
        "What is climate change?",
        "Tell me about artificial intelligence.",
        "Explain quantum computing briefly."
    ]
    
    # Run the agent with each query
    for query in queries:
        print(f"\n\n--- Query: {query} ---")
        try:
            response = await google_agent.run(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    print("Running Google GenAI Example...")
    asyncio.run(main()) 