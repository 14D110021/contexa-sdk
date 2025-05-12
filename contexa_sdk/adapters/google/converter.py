"""Converters for Google ADK integration."""

import inspect
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union, Callable, Type
from pydantic import BaseModel

from contexa_sdk.core.tool import BaseTool, ContexaTool, RemoteTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent, HandoffData

logger = logging.getLogger(__name__)

async def convert_tool_to_google(tool: Union[BaseTool, RemoteTool]) -> Dict[str, Any]:
    """Convert a Contexa tool to Google ADK format.
    
    Args:
        tool: The Contexa tool to convert
    
    Returns:
        Google ADK tool specification
    """
    logger.info(f"Converting Contexa tool {tool.name} to Google ADK format")
    
    try:
        from google.adk.tools import tool as adk_tool
    except ImportError:
        logger.error("Google ADK not installed. Please install google-adk to use this feature.")
        raise ImportError("Google ADK not installed. Please install google-adk to use this feature.")
    
    # Get the tool's signature and input model
    if isinstance(tool, RemoteTool):
        input_model = tool.input_schema
    else:
        input_model = tool.input_type
    
    # Define a function that will be decorated with ADK's @tool decorator
    async def adk_compatible_tool(*args, **kwargs):
        """Tool wrapper for Google ADK compatibility."""
        # Convert kwargs to input model if needed
        if input_model and issubclass(input_model, BaseModel):
            input_instance = input_model(**kwargs)
            result = await tool(input_instance)
        else:
            result = await tool(**kwargs)
        return result
    
    # Create a sync version for ADK compatibility (since ADK often expects sync functions)
    def sync_adk_tool(*args, **kwargs):
        """Synchronous wrapper for the async tool."""
        return asyncio.run(adk_compatible_tool(*args, **kwargs))
    
    # Apply Google ADK's tool decorator with proper name and description
    decorated_tool = adk_tool(
        name=tool.name,
        description=tool.description
    )(sync_adk_tool)
    
    # For debugging
    logger.debug(f"Created ADK tool: {decorated_tool.__name__}")
    
    return decorated_tool

async def convert_model_to_google(model: ContexaModel) -> Any:
    """Convert a Contexa model to Google ADK format.
    
    Args:
        model: The Contexa model to convert
    
    Returns:
        Google ADK model configuration
    """
    try:
        from google.adk import settings
    except ImportError:
        logger.error("Google ADK not installed. Please install google-adk to use this feature.")
        raise ImportError("Google ADK not installed. Please install google-adk to use this feature.")
    
    logger.info(f"Converting Contexa model {model.model_name} to Google ADK model")
    
    # Map the model name to a Google ADK compatible model name
    # Latest Google ADK uses Gemini 2.0 models
    model_mapping = {
        # Current Gemini models
        "gemini-pro": "gemini-2.0-flash",
        "gemini-pro-vision": "gemini-2.0-flash",
        "gemini-ultra": "gemini-2.0-flash",
        
        # Legacy models to current models
        "gemini-1.5-pro": "gemini-2.0-flash",
        "gemini-1.5-pro-vision": "gemini-2.0-flash",
        "gemini-1.5-flash": "gemini-2.0-flash",
        
        # Non-Google models fallback to Gemini
        "gpt-4": "gemini-2.0-flash",
        "gpt-4o": "gemini-2.0-flash",
        "claude-3-opus": "gemini-2.0-flash",
    }
    
    # Get the actual model to use, either direct match or fallback
    adk_model = model_mapping.get(model.model_name, "gemini-2.0-flash")
    
    # Configure temperature and other settings if provided in model.config
    temperature = model.config.get("temperature", 0.7)
    
    # Additional configuration
    model_config = {
        "model": adk_model,
        "temperature": temperature,
    }
    
    # Add API key if provided
    api_key = model.config.get("api_key")
    if api_key:
        model_config["api_key"] = api_key
    
    return model_config

async def convert_agent_to_google(agent: ContexaAgent) -> Any:
    """Convert a Contexa agent to Google ADK agent.
    
    Args:
        agent: The Contexa agent to convert
    
    Returns:
        Google ADK agent instance
    """
    try:
        from google.adk.agents import Agent as ADKAgent
    except ImportError:
        logger.error("Google ADK not installed. Please install google-adk to use this feature.")
        raise ImportError("Google ADK not installed. Please install google-adk to use this feature.")
    
    logger.info(f"Converting Contexa agent {agent.name} to Google ADK agent")
    
    # Convert the model configuration
    model_config = await convert_model_to_google(agent.model)
    
    # Convert all tools
    tools = []
    for tool in agent.tools:
        google_tool = await convert_tool_to_google(tool)
        tools.append(google_tool)
    
    # Prepare the system instruction
    instruction = agent.system_prompt
    if not instruction:
        instruction = f"You are {agent.name}, {agent.description}"
    
    # Create the Google ADK agent
    adk_agent = ADKAgent(
        name=agent.name,
        model=model_config.get("model"),  # Use the mapped model name
        instruction=instruction,
        description=agent.description,
        tools=tools
    )
    
    # Apply temperature if specified
    if "temperature" in model_config:
        adk_agent.temperature = model_config["temperature"]
    
    # Store reference to original Contexa agent
    setattr(adk_agent, "_contexa_agent", agent)
    
    return adk_agent

async def adapt_google_agent(adk_agent: Any) -> ContexaAgent:
    """Adapt a Google ADK agent back to a Contexa agent.
    
    Args:
        adk_agent: The Google ADK agent to adapt
        
    Returns:
        A Contexa agent with equivalent configuration
    """
    # If this agent was originally converted from a Contexa agent, retrieve the original
    if hasattr(adk_agent, "_contexa_agent"):
        return getattr(adk_agent, "_contexa_agent")
    
    try:
        from google.adk.agents import Agent as ADKAgent
    except ImportError:
        logger.error("Google ADK not installed. Please install google-adk to use this feature.")
        raise ImportError("Google ADK not installed. Please install google-adk to use this feature.")
    
    if not isinstance(adk_agent, ADKAgent):
        raise TypeError("The provided object is not a Google ADK Agent")
    
    # Extract the tools from the ADK agent
    contexa_tools = []
    for tool in adk_agent.tools:
        # Create Contexa tool from Google ADK tool
        tool_name = getattr(tool, "name", tool.__name__)
        tool_description = getattr(tool, "description", tool.__doc__ or "")
        
        # Create a ContexaTool
        @ContexaTool.register(name=tool_name, description=tool_description)
        async def contexa_tool(**kwargs):
            return await asyncio.to_thread(tool, **kwargs)
        
        contexa_tools.append(contexa_tool)
    
    # Create the Contexa model
    contexa_model = ContexaModel(
        provider="google",
        model_name=adk_agent.model,
        config={
            "temperature": getattr(adk_agent, "temperature", 0.7)
        }
    )
    
    # Create the Contexa agent
    contexa_agent = ContexaAgent(
        name=adk_agent.name,
        description=adk_agent.description,
        system_prompt=adk_agent.instruction,
        model=contexa_model,
        tools=contexa_tools
    )
    
    return contexa_agent 