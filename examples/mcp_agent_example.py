#!/usr/bin/env python
"""Example demonstrating MCP agent functionality in the Contexa SDK."""

import os
import asyncio
from typing import Dict, List, Any, Optional

from contexa_sdk.core.agent import ContexaAgent, RemoteAgent
from contexa_sdk.core.tool import BaseTool, ToolResult
from contexa_sdk.core.memory import ContexaMemory
from contexa_sdk.core.config import ContexaConfig
from contexa_sdk.deployment.builder import build_agent
from contexa_sdk.deployment.deployer import deploy_agent, list_mcp_agents


# Define a simple tool for the example
class WeatherTool(BaseTool):
    """Tool for getting weather information."""
    
    name = "weather"
    description = "Get weather information for a location"
    
    def __init__(self):
        """Initialize the weather tool."""
        parameters = {
            "location": {
                "type": "string",
                "description": "The location to get weather for",
                "required": True
            },
            "date": {
                "type": "string",
                "description": "The date to get weather for (optional)",
                "required": False
            }
        }
        super().__init__(parameters=parameters)
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the weather tool."""
        location = kwargs.get("location", "")
        date = kwargs.get("date", "today")
        
        # Simulate a weather API call
        weather_data = {
            "location": location,
            "date": date,
            "temperature": 72,
            "condition": "sunny",
            "humidity": 45
        }
        
        return ToolResult(
            result=f"The weather in {location} on {date} is {weather_data['condition']} "
                   f"with a temperature of {weather_data['temperature']}°F "
                   f"and {weather_data['humidity']}% humidity.",
            raw_data=weather_data
        )


# Define a simple restaurant recommendation tool
class RestaurantTool(BaseTool):
    """Tool for recommending restaurants."""
    
    name = "restaurants"
    description = "Get restaurant recommendations for a location"
    
    def __init__(self):
        """Initialize the restaurant tool."""
        parameters = {
            "location": {
                "type": "string", 
                "description": "The location to get restaurants for",
                "required": True
            },
            "cuisine": {
                "type": "string",
                "description": "The type of cuisine (optional)",
                "required": False
            }
        }
        super().__init__(parameters=parameters)
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the restaurant tool."""
        location = kwargs.get("location", "")
        cuisine = kwargs.get("cuisine", "any")
        
        # Simulate a restaurant API call
        if cuisine.lower() == "any":
            restaurants = [
                {"name": "Tasty Bites", "rating": 4.5, "cuisine": "Italian"},
                {"name": "Spice Garden", "rating": 4.3, "cuisine": "Indian"},
                {"name": "Ocean Delights", "rating": 4.7, "cuisine": "Seafood"}
            ]
        else:
            # Filter by cuisine
            restaurants = [
                {"name": "Authentic Flavors", "rating": 4.6, "cuisine": cuisine},
                {"name": "Cuisine Express", "rating": 4.2, "cuisine": cuisine}
            ]
        
        result_text = f"Here are some restaurant recommendations in {location}"
        if cuisine.lower() != "any":
            result_text += f" for {cuisine} cuisine"
        result_text += ":\n"
        
        for restaurant in restaurants:
            result_text += f"- {restaurant['name']} ({restaurant['rating']} stars, {restaurant['cuisine']})\n"
        
        return ToolResult(
            result=result_text,
            raw_data={"location": location, "cuisine": cuisine, "restaurants": restaurants}
        )


async def create_and_deploy_mcp_agents():
    """Create and deploy MCP-compatible agents."""
    # Create the weather agent
    weather_agent = ContexaAgent(
        name="Weather Expert",
        description="An agent specialized in providing weather information for any location",
        tools=[WeatherTool()],
        config=ContexaConfig(),
        agent_id="weather_expert"
    )
    
    # Create the restaurant agent
    restaurant_agent = ContexaAgent(
        name="Restaurant Advisor",
        description="An agent specialized in recommending restaurants based on location and cuisine",
        tools=[RestaurantTool()],
        config=ContexaConfig(),
        agent_id="restaurant_advisor"
    )
    
    # Build and deploy the agents as MCP servers
    # First, create the build directory if it doesn't exist
    os.makedirs("./build", exist_ok=True)
    
    # Build the agents
    print("Building Weather Expert MCP agent...")
    weather_agent_path = build_agent(
        agent=weather_agent,
        output_dir="./build",
        version="0.1.0",
        mcp_compatible=True,  # Make it MCP-compatible
        mcp_version="1.0"
    )
    
    print("Building Restaurant Advisor MCP agent...")
    restaurant_agent_path = build_agent(
        agent=restaurant_agent,
        output_dir="./build",
        version="0.1.0",
        mcp_compatible=True,  # Make it MCP-compatible
        mcp_version="1.0"
    )
    
    # Deploy the agents
    print("Deploying Weather Expert MCP agent...")
    weather_deployment = deploy_agent(
        agent_path=weather_agent_path,
        register_as_mcp=True  # Register in the MCP registry
    )
    
    print("Deploying Restaurant Advisor MCP agent...")
    restaurant_deployment = deploy_agent(
        agent_path=restaurant_agent_path,
        register_as_mcp=True  # Register in the MCP registry
    )
    
    return weather_deployment, restaurant_deployment


async def demonstrate_mcp_agent_usage():
    """Demonstrate using MCP agents through the RemoteAgent class."""
    # First, check if we have any MCP agents deployed
    mcp_agents = list_mcp_agents()
    
    if not mcp_agents:
        print("No MCP agents found. Deploying agents first...")
        weather_deployment, restaurant_deployment = await create_and_deploy_mcp_agents()
        weather_endpoint = weather_deployment["endpoint_url"]
        restaurant_endpoint = restaurant_deployment["endpoint_url"]
    else:
        # Use the first two available MCP agents
        if len(mcp_agents) < 2:
            print("Not enough MCP agents found. Deploying agents first...")
            weather_deployment, restaurant_deployment = await create_and_deploy_mcp_agents()
            weather_endpoint = weather_deployment["endpoint_url"]
            restaurant_endpoint = restaurant_deployment["endpoint_url"]
        else:
            weather_endpoint = mcp_agents[0]["endpoint_url"]
            restaurant_endpoint = mcp_agents[1]["endpoint_url"]
    
    # Initialize the RemoteAgent instances
    print(f"Connecting to weather agent at: {weather_endpoint}")
    weather_agent = await RemoteAgent.from_endpoint(weather_endpoint)
    
    print(f"Connecting to restaurant agent at: {restaurant_endpoint}")
    restaurant_agent = await RemoteAgent.from_endpoint(restaurant_endpoint)
    
    # Use the weather agent
    print("\n--- Weather Agent Interaction ---")
    weather_response = await weather_agent.run("What's the weather like in San Francisco today?")
    print(f"Weather Agent: {weather_response}")
    
    # Use the restaurant agent
    print("\n--- Restaurant Agent Interaction ---")
    restaurant_response = await restaurant_agent.run("Can you recommend some Italian restaurants in New York?")
    print(f"Restaurant Agent: {restaurant_response}")
    
    # Demonstrate an agent handoff
    print("\n--- Agent Handoff Example ---")
    planning_query = """I'm planning a trip to Chicago tomorrow. 
    What's the weather going to be like, and can you recommend some good restaurants?"""
    
    # First, use the weather agent
    print("Step 1: Starting with Weather Agent")
    weather_result = await weather_agent.run(planning_query)
    print(f"Weather Agent: {weather_result}")
    
    # Then, hand off to the restaurant agent
    print("Step 2: Handing off to Restaurant Agent")
    restaurant_result = await weather_agent.handoff_to(
        target_agent=restaurant_agent,
        query="Based on the weather information, what restaurants would you recommend in Chicago?",
        include_history=True  # Include the conversation history in the handoff
    )
    print(f"Restaurant Agent: {restaurant_result}")
    
    return weather_agent, restaurant_agent


async def main():
    """Run the MCP agent example."""
    print("=== MCP Agent Example ===")
    print("This example demonstrates how to create, deploy, and use MCP-compatible agents.")
    
    try:
        weather_agent, restaurant_agent = await demonstrate_mcp_agent_usage()
        print("\nExample completed successfully!")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 