"""Example demonstrating agent handoffs across different frameworks."""

import asyncio
from typing import Dict, List, Any
from pydantic import BaseModel

from contexa_sdk.core.tool import ContexaTool, RemoteTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.adapters import langchain, crewai, openai, google_adk


# Define tools for our agents
class SearchInput(BaseModel):
    """Input for the web search tool."""
    query: str


class LocationInput(BaseModel):
    """Input for location-based tools."""
    location: str


@ContexaTool.register(
    name="web_search",
    description="Search the web and return the top result"
)
async def web_search(inp: SearchInput) -> str:
    """Search the web and return the top result."""
    # In a real implementation, this would make a request to a search API
    return f"Top result for '{inp.query}': This is a simulated search result."


@ContexaTool.register(
    name="get_weather",
    description="Get the current weather for a location"
)
async def get_weather(inp: LocationInput) -> str:
    """Get the current weather for a location."""
    # In a real implementation, this would make a request to a weather API
    return f"Weather for '{inp.location}': Sunny, 75°F"


@ContexaTool.register(
    name="get_restaurants",
    description="Get restaurant recommendations for a location"
)
async def get_restaurants(inp: LocationInput) -> str:
    """Get restaurant recommendations for a location."""
    # In a real implementation, this would make a request to a restaurant API
    return f"Restaurants in '{inp.location}': 1. Fine Dining, 2. Casual Café, 3. Street Food"


# Create models for our agents
search_model = ContexaModel(
    model_name="gpt-4o",
    provider="openai",
)

weather_model = ContexaModel(
    model_name="claude-3-sonnet-20240229",
    provider="anthropic",
)

restaurant_model = ContexaModel(
    model_name="gpt-4o",
    provider="openai",
)

# Create agents with different specializations
search_agent = ContexaAgent(
    tools=[web_search.__contexa_tool__],
    model=search_model,
    name="search_agent",
    description="An agent that can search the web",
    system_prompt="You are a helpful search assistant. You excel at finding information on the web.",
)

weather_agent = ContexaAgent(
    tools=[get_weather.__contexa_tool__],
    model=weather_model,
    name="weather_agent",
    description="An agent that can get weather information",
    system_prompt="You are a weather expert. You provide accurate weather information for locations.",
)

restaurant_agent = ContexaAgent(
    tools=[get_restaurants.__contexa_tool__],
    model=restaurant_model,
    name="restaurant_agent",
    description="An agent that can recommend restaurants",
    system_prompt="You are a food critic with extensive knowledge of restaurants worldwide.",
)

# Convert agents to framework-specific agents
lc_weather_agent = langchain.agent(weather_agent)
crew_restaurant_agent = crewai.agent(restaurant_agent)
openai_search_agent = openai.agent(search_agent)

# Example of handoffs across frameworks
async def demonstrate_handoffs():
    """Demonstrate handoffs between agents in different frameworks."""
    print("=" * 50)
    print("AGENT HANDOFF EXAMPLE")
    print("=" * 50)
    
    # Scenario: A user wants to plan a trip to San Francisco
    initial_query = "I'm planning a trip to San Francisco. Can you help me?"
    
    print(f"\nInitial query to search agent: {initial_query}")
    # First, the search agent provides general information
    search_result = await search_agent.run(initial_query)
    print(f"\nSearch Agent response: {search_result}")
    
    # Then, hand off to the weather agent (LangChain) for weather information
    print("\n[Handing off to LangChain weather agent for weather information]")
    weather_query = "What's the weather like in San Francisco this week?"
    
    # Using the adapter-specific handoff method
    weather_result = await langchain.handoff(
        source_agent=search_agent,
        target_agent_executor=lc_weather_agent,
        query=weather_query,
        context={"previous_response": search_result},
        metadata={"reason": "Need weather information"}
    )
    print(f"\nLangChain Weather Agent response: {weather_result}")
    
    # Next, hand off to the restaurant agent (CrewAI) for food recommendations
    print("\n[Handing off to CrewAI restaurant agent for restaurant recommendations]")
    restaurant_query = "What are the best restaurants to try in San Francisco?"
    
    # Using the adapter-specific handoff method
    restaurant_result = await crewai.handoff(
        source_agent=weather_agent,
        target_crew=crew_restaurant_agent,
        query=restaurant_query,
        context={
            "previous_search": search_result,
            "weather_info": weather_result
        },
        metadata={"reason": "Need restaurant recommendations"}
    )
    print(f"\nCrewAI Restaurant Agent response: {restaurant_result}")
    
    # Finally, hand off back to the search agent (OpenAI) to compile the travel plan
    print("\n[Handing off to OpenAI search agent to compile the travel plan]")
    final_query = "Based on the weather and restaurant information, can you suggest a 3-day itinerary for San Francisco?"
    
    # Using the adapter-specific handoff method
    final_result = await openai.handoff(
        source_agent=restaurant_agent,
        target_agent=openai_search_agent,
        query=final_query,
        context={
            "weather_info": weather_result,
            "restaurant_info": restaurant_result
        },
        metadata={"reason": "Need final itinerary"}
    )
    print(f"\nFinal Itinerary from OpenAI Search Agent: {final_result}")
    
    # Show that handoff data is recorded in each agent's memory
    print("\n" + "=" * 50)
    print("HANDOFF HISTORY")
    print("=" * 50)
    
    print(f"\nSearch Agent has {len(search_agent.memory.handoff_history)} handoff records")
    print(f"Weather Agent has {len(weather_agent.memory.handoff_history)} handoff records")
    print(f"Restaurant Agent has {len(restaurant_agent.memory.handoff_history)} handoff records")
    
    # Example of direct handoff using ContexaAgent.handoff_to method
    print("\n" + "=" * 50)
    print("DIRECT HANDOFF BETWEEN CONTEXA AGENTS")
    print("=" * 50)
    
    direct_query = "What's the weather like in New York?"
    print(f"\nDirect handoff from search agent to weather agent: {direct_query}")
    
    direct_result = await search_agent.handoff_to(
        target_agent=weather_agent,
        query=direct_query
    )
    
    print(f"\nDirect handoff result: {direct_result}")
    
    # Final status
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print("Successfully demonstrated handoffs across:")
    print("1. ContexaAgent → LangChain AgentExecutor")
    print("2. LangChain → CrewAI Crew")
    print("3. CrewAI → OpenAI Agent")
    print("4. Direct ContexaAgent → ContexaAgent")


if __name__ == "__main__":
    asyncio.run(demonstrate_handoffs()) 