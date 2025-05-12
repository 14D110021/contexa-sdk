"""
Example demonstrating OpenAI thread management with Contexa SDK.

This example shows how to:
1. Create and use OpenAI threads with Contexa agents
2. Perform thread-based handoffs between OpenAI Assistants
3. Preserve conversation context across multiple agents

This implementation combines the OpenAI Assistants API with Contexa's agent framework,
allowing for sophisticated conversation management and handoffs.
"""

import asyncio
import os
from typing import Dict, List, Any
from pydantic import BaseModel

# Import from Contexa SDK
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent, HandoffData

# Import OpenAI adapter with thread management
from contexa_sdk.adapters import openai
from contexa_sdk.adapters.openai.thread import (
    get_thread_for_agent,
    memory_to_thread,
    thread_to_memory,
)


# Define input class for tools
class SearchInput(BaseModel):
    query: str


# Define a tool
@ContexaTool.register(
    name="web_search",
    description="Search the web for information on a topic"
)
async def web_search(inp: SearchInput) -> str:
    """Search the web for information on a topic."""
    # Simulate a web search API call
    await asyncio.sleep(1)
    return f"Search results for '{inp.query}': Found information about trends, statistics, and analysis."


async def demonstrate_openai_thread_integration():
    """Demonstrate OpenAI thread management with Contexa SDK."""
    print("🧵 OpenAI Thread Management Example")
    
    # Create a Contexa agent
    research_agent = ContexaAgent(
        name="Research Agent",
        description="A helpful research assistant",
        model=ContexaModel(provider="openai", model_name="gpt-4o"),
        tools=[web_search],
        system_prompt="You are a research assistant specialized in finding information."
    )
    
    # Convert to OpenAI agent (this automatically creates a thread)
    try:
        print("\n🔄 Converting Contexa agent to OpenAI agent (with thread)...")
        openai_agent = openai.agent(research_agent)
        print("✅ Successfully converted to OpenAI agent with thread")
        
        # Display thread information
        thread_id = getattr(openai_agent, "__thread_id__", "Unknown")
        print(f"📋 Thread ID: {thread_id}")
        
        # Run the agent to populate the thread
        print("\n🤖 Running the agent...")
        query = "What are the latest trends in AI?"
        
        try:
            from agents import Runner
            result = await Runner.run(openai_agent, query)
            print(f"🔍 Response: {result.final_output}")
            
            # Convert agent's memory to thread
            updated_thread_id = memory_to_thread(research_agent)
            print(f"📋 Updated Thread ID: {updated_thread_id}")
            
            # Create a new agent based on an existing OpenAI Assistant
            # Note: You need to replace this with an actual Assistant ID
            assistant_id = os.environ.get("OPENAI_ASSISTANT_ID")
            if assistant_id:
                print("\n🔄 Creating Contexa agent from OpenAI Assistant...")
                assistant_agent = await openai.adapt_assistant(assistant_id)
                print(f"✅ Successfully created agent from Assistant: {assistant_agent.name}")
                
                # Hand off to the assistant using thread-based communication
                print("\n🔄 Performing thread-based handoff...")
                handoff_query = "Can you summarize these AI trends in 3 bullet points?"
                handoff_context = {"research_results": str(result.final_output)}
                
                # Perform the handoff
                handoff_result = await openai.handoff(
                    source_agent=research_agent,
                    target_agent=assistant_agent,
                    query=handoff_query,
                    context=handoff_context
                )
                
                print(f"🔍 Handoff Result: {handoff_result}")
            else:
                print("\n⚠️ No OPENAI_ASSISTANT_ID environment variable found. Skipping Assistant demo.")
                print("   To test with an actual Assistant, set OPENAI_ASSISTANT_ID environment variable.")
        
        except Exception as e:
            print(f"❌ Error running agent: {str(e)}")
            print("   This may be due to missing OpenAI credentials or permissions.")
            
    except ImportError:
        print("❌ OpenAI SDK not installed. Install with `pip install openai` and `pip install agents`")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n✅ OpenAI thread integration example completed")


if __name__ == "__main__":
    asyncio.run(demonstrate_openai_thread_integration()) 