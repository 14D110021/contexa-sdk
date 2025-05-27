"""Google ADK adapter for converting Contexa objects to Google Agent Development Kit objects.

This adapter provides integration between Contexa SDK and Google's Agent Development Kit (ADK),
which offers advanced agent capabilities beyond simple model interaction. It converts Contexa
tools, models, agents, and prompts to their Google ADK equivalents.

The adapter supports:
- Converting ContexaTool objects to Google ADK tool declarations
- Adapting Contexa agent configurations to Google ADK agents
- Creating agent wrappers that leverage Google ADK's advanced reasoning capabilities
- Handling complex agent execution with multi-step reasoning
- Facilitating handoffs between Contexa agents and Google ADK agents

Usage:
    from contexa_sdk.adapters.google import adk_tool, adk_agent, adk_handoff

    # Convert a Contexa agent to a Google ADK agent
    google_agent = adk_agent(my_contexa_agent)
    
    # Run the Google ADK agent
    result = await google_agent.run("Perform a complex analysis on this data set")
    
    # Handle a handoff to an ADK agent
    response = await adk_handoff(
        source_agent=my_source_agent,
        target_adk_agent=google_agent,
        query="Continue this analysis with advanced reasoning",
        context={"previous_results": "Initial findings..."}
    )

Requirements:
    This adapter requires the Google ADK SDK to be installed:
    `pip install contexa-sdk[google-adk]` or `pip install google-adk`

When to use this adapter:
    Use the ADK adapter when you need advanced agent capabilities like:
    - Complex multi-step reasoning
    - Sophisticated task decomposition
    - Advanced planning capabilities
    - Integration with Google's agent ecosystem
    
    For simpler model interactions with Gemini models, consider using the
    Google GenAI adapter instead (from contexa_sdk.adapters.google import genai_*).
"""

import inspect
import asyncio
import json
from typing import Any, Dict, List, Optional, Union, Callable
import logging

from contexa_sdk.core.agent import ContexaAgent, HandoffData
from contexa_sdk.core.model import ModelMessage
from contexa_sdk.core.tool import ContexaTool

# Adapter version
__adapter_version__ = "0.1.0"

# Set up logging
logger = logging.getLogger(__name__)

class ADKManager:
    """Manages Google ADK integration for Contexa agents."""
    
    def __init__(self, client=None):
        """Initialize the ADK manager.
        
        Args:
            client: Optional Google ADK client instance. If not provided, 
                   a new client will be created when needed.
        """
        self._client = client
        self._agent_cache = {}  # agent_id -> adk_agent mapping
    
    @property
    def client(self):
        """Get the Google ADK client instance."""
        if self._client is None:
            try:
                # Import Google ADK SDK when needed
                from google.ai.generativelanguage import AgentServiceClient
                from google.auth import default
                
                # Create a client with default credentials
                credentials, _ = default()
                self._client = AgentServiceClient(credentials=credentials)
            except ImportError:
                raise ImportError("Google ADK SDK not found. Install with `pip install google-cloud-aiplatform`.")
        return self._client
    
    def contexa_to_adk(self, agent: ContexaAgent) -> Any:
        """Convert a Contexa agent to a Google ADK agent.
        
        Args:
            agent: The Contexa agent to convert
            
        Returns:
            The Google ADK agent instance
        """
        if agent.agent_id in self._agent_cache:
            return self._agent_cache[agent.agent_id]
        
        # Import necessary Google ADK classes
        try:
            from google.ai.generativelanguage import Agent, AgentServiceClient, Tool
            from google.ai.generativelanguage import Content, Part, FunctionCallingConfig
        except ImportError:
            raise ImportError("Google ADK SDK not found. Install with `pip install google-cloud-aiplatform`.")
        
        # Convert Contexa tools to Google ADK tools
        adk_tools = []
        for tool in agent.tools:
            # Convert the tool to Google ADK format
            # This is a simplified implementation; real implementation would need to
            # handle the full conversion of tool schemas, etc.
            adk_tool = Tool(
                name=tool.name,
                description=tool.description,
                # Additional tool configuration would be needed here
            )
            adk_tools.append(adk_tool)
        
        # Create ADK agent with the converted properties
        adk_agent = Agent(
            display_name=agent.name,
            description=agent.description,
            tools=adk_tools
        )
        
        # Store in cache
        self._agent_cache[agent.agent_id] = adk_agent
        
        return adk_agent
    
    def adk_to_contexa(self, adk_agent: Any) -> ContexaAgent:
        """Convert a Google ADK agent to a Contexa agent.
        
        Args:
            adk_agent: The Google ADK agent to convert
            
        Returns:
            A new Contexa agent
        """
        # Import necessary Google ADK classes
        try:
            from google.ai.generativelanguage import Agent
        except ImportError:
            raise ImportError("Google ADK SDK not found. Install with `pip install google-cloud-aiplatform`.")
        
        # Extract basic properties
        name = adk_agent.display_name
        description = adk_agent.description
        
        # Convert ADK tools to Contexa tools
        contexa_tools = []
        # Tool conversion would be implemented here
        
        # Create a new Contexa agent
        contexa_agent = ContexaAgent(
            name=name,
            description=description,
            tools=contexa_tools
        )
        
        return contexa_agent
    
    async def run_adk_agent(self, adk_agent: Any, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run a Google ADK agent with the given query.
        
        Args:
            adk_agent: The Google ADK agent to run
            query: The user query to process
            context: Optional context for the agent
            
        Returns:
            The agent response
        """
        # Import necessary Google ADK classes
        try:
            from google.ai.generativelanguage import GenerateContentRequest, Content, Part
        except ImportError:
            raise ImportError("Google ADK SDK not found. Install with `pip install google-cloud-aiplatform`.")
        
        # Prepare the request with context if provided
        parts = [Part(text=query)]
        if context:
            context_str = json.dumps(context)
            parts.append(Part(text=f"Context: {context_str}"))
        
        content = Content(parts=parts)
        request = GenerateContentRequest(
            agent=adk_agent.name,
            content=content
        )
        
        # Call the ADK agent
        response = self.client.generate_content(request)
        
        # Process and return the response
        # This is simplified; a real implementation would handle different response types
        response_text = response.candidates[0].content.parts[0].text
        return {"response": response_text}
        
    async def handoff_to_adk(self, handoff_data: HandoffData, target_adk_agent: Any) -> str:
        """Handle a handoff to a Google ADK agent.
        
        Args:
            handoff_data: The handoff data from the source agent
            target_adk_agent: The target Google ADK agent
            
        Returns:
            The response from the target agent
        """
        # Run the ADK agent with the handoff data
        result = await self.run_adk_agent(
            adk_agent=target_adk_agent,
            query=handoff_data.query,
            context=handoff_data.context
        )
        
        return result.get("response", "No response from ADK agent.")


# Create a singleton ADK manager
adk_manager = ADKManager()

# Export functions
async def adapt_agent(agent: ContexaAgent) -> Any:
    """Convert a Contexa agent to a Google ADK agent."""
    return adk_manager.contexa_to_adk(agent)

# Synchronous wrapper for adapt_agent
def sync_adapt_agent(agent: ContexaAgent) -> Any:
    """Synchronous wrapper for adapt_agent."""
    try:
        import asyncio
        return asyncio.run(adapt_agent(agent))
    except Exception as e:
        logger.error(f"Error adapting agent: {str(e)}")
        raise e

async def adapt_adk_agent(adk_agent_id: str) -> ContexaAgent:
    """Convert a Google ADK agent to a Contexa agent."""
    # Fetch the ADK agent
    adk_agent = adk_manager.client.get_agent(name=adk_agent_id)
    return adk_manager.adk_to_contexa(adk_agent)

# Synchronous wrapper for adapt_adk_agent
def sync_adapt_adk_agent(adk_agent_id: str) -> ContexaAgent:
    """Synchronous wrapper for adapt_adk_agent."""
    try:
        import asyncio
        return asyncio.run(adapt_adk_agent(adk_agent_id))
    except Exception as e:
        logger.error(f"Error adapting ADK agent: {str(e)}")
        raise e

async def handoff(source_agent: ContexaAgent, target_adk_agent: Any, 
                query: str, context: Dict[str, Any] = None) -> str:
    """Handle a handoff to a Google ADK agent."""
    handoff_data = HandoffData(
        source_agent_id=source_agent.agent_id,
        source_agent_name=source_agent.name,
        query=query,
        context=context or {}
    )
    return await adk_manager.handoff_to_adk(handoff_data, target_adk_agent)

# Synchronous wrapper for handoff
def sync_handoff(source_agent: ContexaAgent, target_adk_agent: Any, 
               query: str, context: Dict[str, Any] = None) -> str:
    """Synchronous wrapper for handoff."""
    try:
        import asyncio
        return asyncio.run(handoff(
            source_agent=source_agent,
            target_adk_agent=target_adk_agent,
            query=query,
            context=context
        ))
    except Exception as e:
        logger.error(f"Error in handoff: {str(e)}")
        raise e

async def run(adk_agent: Any, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run a Google ADK agent with the given query."""
    return await adk_manager.run_adk_agent(adk_agent, query, context)

# Synchronous wrapper for run
def sync_run(adk_agent: Any, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Synchronous wrapper for run."""
    try:
        import asyncio
        return asyncio.run(run(
            adk_agent=adk_agent,
            query=query,
            context=context
        ))
    except Exception as e:
        logger.error(f"Error running agent: {str(e)}")
        raise e 