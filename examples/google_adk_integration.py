"""
Example demonstrating Google ADK integration with Contexa SDK.

This example shows how to:
1. Convert Contexa agents to Google ADK agents
2. Adapt existing Google ADK agents to Contexa
3. Perform handoffs between Contexa and Google ADK agents
4. Run Google ADK agents with the Contexa SDK

This implementation combines Google's Agent Development Kit with Contexa's agent framework,
allowing for seamless interoperability between the two systems.
"""

import asyncio
import os
from typing import Dict, List, Any
from pydantic import BaseModel

# Import from Contexa SDK
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent

# Import Google adapter with ADK integration
from contexa_sdk.adapters import google
from contexa_sdk.adapters.google.adk import adapt_agent, adapt_adk_agent, handoff, run


# Define input class for tools
class SearchInput(BaseModel):
    query: str


# Define a tool
@ContexaTool.register(
    name="knowledge_search",
    description="Search knowledge base for information on a topic"
)
async def knowledge_search(inp: SearchInput) -> str:
    """Search the knowledge base for information on a topic."""
    # Simulate a knowledge search
    await asyncio.sleep(1)
    return f"Knowledge base results for '{inp.query}': Found relevant information in internal documents."


async def demonstrate_google_adk_integration():
    """Demonstrate Google ADK integration with Contexa SDK."""
    print("🤖 Google ADK Integration Example")
    
    # Create a Contexa agent
    research_agent = ContexaAgent(
        name="Research Assistant",
        description="A research assistant specialized in finding information from internal knowledge bases",
        model=ContexaModel(provider="google", model_name="gemini-pro"),
        tools=[knowledge_search],
        system_prompt="You are a research assistant with access to internal knowledge bases."
    )
    
    # Convert to Google ADK agent
    try:
        print("\n🔄 Converting Contexa agent to Google ADK agent...")
        try:
            adk_agent = await adapt_agent(research_agent)
            print("✅ Successfully converted to Google ADK agent")
            
            # Run the ADK agent
            print("\n🤖 Running the ADK agent...")
            query = "What are our company's sustainability initiatives?"
            
            try:
                result = await run(adk_agent, query)
                print(f"🔍 Response: {result.get('response', 'No response')}")
                
                # Use an existing Google ADK agent (if available)
                adk_agent_id = os.environ.get("GOOGLE_ADK_AGENT_ID")
                if adk_agent_id:
                    print("\n🔄 Creating Contexa agent from Google ADK agent...")
                    try:
                        adapted_agent = await adapt_adk_agent(adk_agent_id)
                        print(f"✅ Successfully created agent from ADK: {adapted_agent.name}")
                        
                        # Perform a handoff between agents
                        print("\n🔄 Performing handoff to ADK agent...")
                        handoff_query = "Can you summarize the sustainability initiatives in a presentation format?"
                        handoff_context = {"research_results": str(result.get('response', ''))}
                        
                        # Execute the handoff
                        handoff_result = await handoff(
                            source_agent=research_agent,
                            target_adk_agent=adk_agent,
                            query=handoff_query,
                            context=handoff_context
                        )
                        
                        print(f"🔍 Handoff Result: {handoff_result}")
                    except Exception as e:
                        print(f"❌ Error adapting ADK agent: {str(e)}")
                else:
                    print("\n⚠️ No GOOGLE_ADK_AGENT_ID environment variable found. Skipping ADK agent adaptation demo.")
                    print("   To test with an actual ADK agent, set GOOGLE_ADK_AGENT_ID environment variable.")
                    
                    # Demonstrate handoff to the same ADK agent we created
                    print("\n🔄 Performing handoff to our converted ADK agent...")
                    handoff_query = "Can you summarize the sustainability initiatives in a presentation format?"
                    handoff_context = {"research_results": str(result.get('response', ''))}
                    
                    # Execute the handoff
                    handoff_result = await handoff(
                        source_agent=research_agent,
                        target_adk_agent=adk_agent,
                        query=handoff_query,
                        context=handoff_context
                    )
                    
                    print(f"🔍 Handoff Result: {handoff_result}")
            
            except Exception as e:
                print(f"❌ Error running ADK agent: {str(e)}")
        
        except ImportError:
            print("❌ Google ADK SDK not installed. Install with `pip install google-cloud-aiplatform`")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error in ADK integration: {str(e)}")
    
    print("\n✅ Google ADK integration example completed")


def check_google_credentials():
    """Check if Google credentials are available."""
    try:
        from google.auth import default
        try:
            credentials, _ = default()
            if credentials is None:
                print("⚠️ No Google credentials found.")
                print("   To use this example, set up Google application credentials:")
                print("   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json")
                return False
            return True
        except Exception:
            print("⚠️ Error loading Google credentials.")
            print("   To use this example, set up Google application credentials:")
            print("   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json")
            return False
    except ImportError:
        print("⚠️ Google auth package not installed.")
        print("   Install with: pip install google-auth")
        return False


if __name__ == "__main__":
    # Check for Google credentials
    has_credentials = check_google_credentials()
    
    # If credentials are available or user wants to continue anyway
    if has_credentials or input("Run example anyway? (y/n): ").lower() == "y":
        asyncio.run(demonstrate_google_adk_integration()) 