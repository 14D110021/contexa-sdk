"""
Google Adapter Migration Example

This example demonstrates how to migrate from the old Google adapter structure 
to the new structure with separate GenAI and ADK implementations.

The example shows:
1. How code would look with the old structure
2. How to migrate to the explicit GenAI adapter
3. How to migrate to the explicit ADK adapter
4. How to use both adapters in the same application

Requirements:
- For GenAI: pip install contexa-sdk[google-genai]
- For ADK: pip install contexa-sdk[google-adk]
- For both: pip install contexa-sdk[google]
"""

import asyncio
from typing import List, Dict
from pydantic import BaseModel

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool

# --------- DEFINE TOOLS ---------

class SearchInput(BaseModel):
    query: str
    limit: int = 5

@ContexaTool.register(
    name="web_search",
    description="Search the web for information"
)
async def web_search(inp: SearchInput) -> str:
    """Simulate a web search."""
    return f"Found {inp.limit} results for '{inp.query}'"

class AnalysisInput(BaseModel):
    data: str
    analysis_type: str = "standard"

@ContexaTool.register(
    name="analyze_data",
    description="Perform data analysis on a dataset"
)
async def analyze_data(inp: AnalysisInput) -> Dict[str, any]:
    """Simulate a data analysis."""
    return {
        "result": f"Analysis of '{inp.data}' using {inp.analysis_type} method",
        "confidence": 0.95
    }

# --------- EXAMPLE 1: OLD APPROACH ---------

async def old_approach():
    """Demonstrate how code would look with the old structure."""
    print("\n===== OLD APPROACH (BEFORE MIGRATION) =====")
    
    # Import the Google adapter (old way - unclear which implementation)
    try:
        from contexa_sdk.adapters import google
        # This would have previously imported from google_genai.py and/or google_adk.py
        
        # Create a Contexa agent
        agent = ContexaAgent(
            name="Assistant",
            description="A helpful assistant",
            model=ContexaModel(provider="google", model_name="gemini-pro"),
            tools=[web_search, analyze_data]
        )
        
        # Convert to Google agent (was unclear which implementation)
        google_agent = google.agent(agent)
        
        print("✓ Created Google agent (implementation was unclear)")
        print("  This used to import from mixed sources with unclear implementation details")
        
    except ImportError:
        print("× Old structure no longer available (files have been removed)")
        print("  The old implementation has been replaced with the new structure")

# --------- EXAMPLE 2: MIGRATING TO GENAI ---------

async def migrate_to_genai():
    """Demonstrate migrating to the explicit GenAI adapter."""
    print("\n===== MIGRATING TO GOOGLE GENAI =====")
    
    # Import the Google GenAI adapter explicitly
    from contexa_sdk.adapters.google import genai_agent
    
    # Create a Contexa agent
    agent = ContexaAgent(
        name="GenAI Assistant",
        description="A helpful assistant using Google GenAI",
        model=ContexaModel(provider="google", model_name="gemini-pro"),
        tools=[web_search]
    )
    
    # Convert to Google GenAI agent (explicit)
    genai_assistant = genai_agent(agent)
    
    print("✓ Created Google GenAI agent (explicit implementation)")
    print("  - Best for: Simple interactions, direct model access")
    print("  - Simpler integration, lightweight, faster setup")
    
    # Example query - would be run in a real implementation
    query = "What's the weather in New York?"
    print(f"\nExample query: '{query}'")
    print("Response would be handled by the GenAI implementation")

# --------- EXAMPLE 3: MIGRATING TO ADK ---------

async def migrate_to_adk():
    """Demonstrate migrating to the explicit ADK adapter."""
    print("\n===== MIGRATING TO GOOGLE ADK =====")
    
    # Import the Google ADK adapter explicitly
    from contexa_sdk.adapters.google import adk_agent
    
    # Create a Contexa agent
    agent = ContexaAgent(
        name="ADK Assistant",
        description="A sophisticated assistant using Google ADK",
        model=ContexaModel(provider="google", model_name="gemini-pro"),
        tools=[web_search, analyze_data]
    )
    
    # Convert to Google ADK agent (explicit)
    adk_assistant = adk_agent(agent)
    
    print("✓ Created Google ADK agent (explicit implementation)")
    print("  - Best for: Complex reasoning, advanced agent capabilities")
    print("  - Better for multi-step tasks, sophisticated planning")
    
    # Example query - would be run in a real implementation
    query = "Analyze the financial data and provide insights"
    print(f"\nExample query: '{query}'")
    print("Response would be handled by the ADK implementation with advanced reasoning")

# --------- EXAMPLE 4: USING BOTH ADAPTERS ---------

async def using_both_adapters():
    """Demonstrate using both adapters in the same application."""
    print("\n===== USING BOTH ADAPTERS =====")
    
    # Import both adapters explicitly
    from contexa_sdk.adapters.google import genai_agent, adk_agent
    
    # Create a simple agent for GenAI
    simple_agent = ContexaAgent(
        name="Simple Assistant",
        description="A simple assistant for basic tasks",
        model=ContexaModel(provider="google", model_name="gemini-pro"),
        tools=[web_search]
    )
    
    # Create a complex agent for ADK
    complex_agent = ContexaAgent(
        name="Advanced Assistant",
        description="An advanced assistant for complex tasks",
        model=ContexaModel(provider="google", model_name="gemini-pro"),
        tools=[web_search, analyze_data]
    )
    
    # Convert to specific implementations
    genai_assistant = genai_agent(simple_agent)
    adk_assistant = adk_agent(complex_agent)
    
    print("✓ Created both GenAI and ADK agents in the same application")
    print("  - Using GenAI for simple queries")
    print("  - Using ADK for complex analysis tasks")
    
    # Example queries - would be run in a real implementation
    simple_query = "What's trending in AI today?"
    complex_query = "Analyze market trends and predict next quarter performance"
    
    print(f"\nSimple query for GenAI: '{simple_query}'")
    print(f"Complex query for ADK: '{complex_query}'")
    print("Each query would be handled by the appropriate implementation")

# --------- MAIN EXECUTION ---------

async def main():
    print("\n===== GOOGLE ADAPTER MIGRATION EXAMPLE =====")
    print("This example demonstrates how to migrate from the old structure to the new one")
    
    # Run all examples
    await old_approach()
    await migrate_to_genai()
    await migrate_to_adk()
    await using_both_adapters()
    
    print("\n===== MIGRATION SUMMARY =====")
    print("1. Update imports to use explicit adapters:")
    print("   from contexa_sdk.adapters.google import genai_agent, adk_agent")
    print("\n2. Choose the right adapter for your use case:")
    print("   - GenAI: Simple interactions, direct model access")
    print("   - ADK: Complex reasoning, advanced agent capabilities")
    print("\n3. Update dependencies:")
    print("   pip install contexa-sdk[google-genai]  # For GenAI")
    print("   pip install contexa-sdk[google-adk]    # For ADK")
    print("   pip install contexa-sdk[google]        # For both")

if __name__ == "__main__":
    asyncio.run(main()) 