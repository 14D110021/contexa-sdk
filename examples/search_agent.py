"""Example of a search agent using the Contexa SDK."""

import asyncio
from pydantic import BaseModel

from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.adapters import langchain, crewai, openai


# Define a tool
class SearchInput(BaseModel):
    """Input for the web search tool."""
    
    query: str


@ContexaTool.register(
    name="web_search",
    description="Search the web and return the top result"
)
async def web_search(inp: SearchInput) -> str:
    """Search the web and return the top result."""
    # In a real implementation, this would make a request to a search API
    return f"Top result for '{inp.query}': This is a simulated search result."


@ContexaTool.register(
    name="weather",
    description="Get the current weather for a location"
)
async def get_weather(inp: SearchInput) -> str:
    """Get the current weather for a location."""
    # In a real implementation, this would make a request to a weather API
    return f"Weather for '{inp.query}': Sunny, 75°F"


# Create a model
model = ContexaModel(
    model_name="gpt-4o",
    provider="openai",
)

# Create an agent using the tools and model
agent = ContexaAgent(
    tools=[web_search.__contexa_tool__, get_weather.__contexa_tool__],
    model=model,
    name="search_agent",
    description="An agent that can search the web and get weather information",
    system_prompt="You are a helpful search assistant. You can search the web and get weather information.",
)

# Example of using the agent directly
async def run_example():
    """Run an example query through the agent."""
    response = await agent.run("What's the weather like in San Francisco?")
    print(f"Direct agent response: {response}\n")
    
    # Example of using LangChain adapter
    print("Converting to LangChain...")
    lc_agent = langchain.agent(agent)
    lc_response = await asyncio.to_thread(
        lc_agent.invoke, 
        "Tell me about the Golden Gate Bridge."
    )
    print(f"LangChain agent response: {lc_response['output']}\n")
    
    # Example of using CrewAI adapter
    print("Converting to CrewAI...")
    crew_agent = crewai.agent(agent)
    crew_response = await asyncio.to_thread(
        crew_agent.kickoff,
        "What's the tallest building in New York City?"
    )
    print(f"CrewAI agent response: {crew_response}\n")
    
    # Example of using OpenAI adapter
    print("Converting to OpenAI Agents SDK...")
    oa_agent = openai.agent(agent)
    oa_response = await oa_agent.run("Who won the latest World Series?")
    print(f"OpenAI agent response: {oa_response}\n")


if __name__ == "__main__":
    # Required for the CLI to find the agent
    __contexa_agent__ = agent
    
    # Run the example
    asyncio.run(run_example()) 