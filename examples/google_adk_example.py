"""
Example of using the Google ADK adapter in Contexa SDK.

This example demonstrates how to use Google's Agent Development Kit (ADK)
with Contexa SDK's adapter system.

Requirements:
- google-adk package: pip install google-adk
"""

import asyncio
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.adapters.google import adk_model, adk_tool, adk_agent


# Define a simple calculator tool
class CalculatorInput:
    expression: str

@ContexaTool.register(
    name="calculator",
    description="Evaluate a mathematical expression"
)
async def calculator(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    try:
        # Simple expression evaluation - in a real app you would use a safer method
        allowed_chars = set("0123456789+-*/() .")
        if any(c not in allowed_chars for c in expression):
            return "Expression contains invalid characters. Only numbers and basic operators (+ - * /) are allowed."
        
        # Evaluate the expression
        result = eval(expression)
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"


async def main():
    # Create a Contexa model for Google ADK
    # Note: ADK typically works with specific model configurations
    model = ContexaModel(
        provider="google",
        model_name="gemini-1.5-pro",  # Use your preferred model that works with ADK
        config={}
    )
    
    # Create a Contexa agent with the model and calculator tool
    agent = ContexaAgent(
        name="Math Assistant",
        description="A helpful assistant that can perform mathematical calculations",
        model=model,
        tools=[calculator],
        system_prompt="You are a math assistant. Use the calculator tool to help users solve mathematical problems."
    )
    
    # Convert the agent to a Google ADK agent
    adk_agent_instance = adk_agent(agent)
    
    # Example queries to run
    calculations = [
        "What is 125 * 37?",
        "Calculate (512 - 64) / 8.",
        "What's the result of 2.5 * 4.5?"
    ]
    
    # Run the agent with each calculation query
    for query in calculations:
        print(f"\n\n--- Query: {query} ---")
        try:
            response = await adk_agent_instance.run(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    print("Running Google ADK Example...")
    asyncio.run(main()) 