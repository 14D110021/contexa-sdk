"""Converters for CrewAI integration."""

import asyncio
import json
import inspect
from typing import Any, Dict, List, Optional, Union, Callable

from contexa_sdk.core.tool import BaseTool, RemoteTool
from contexa_sdk.core.model import ContexaModel, ModelMessage
from contexa_sdk.core.agent import ContexaAgent, RemoteAgent
from contexa_sdk.observability import get_logger, trace, SpanKind

# Create a logger for this module
logger = get_logger(__name__)


@trace(kind=SpanKind.INTERNAL)
async def convert_tool_to_crewai(tool: Union[BaseTool, RemoteTool]) -> Any:
    """Convert a Contexa tool to CrewAI format.
    
    Args:
        tool: The Contexa tool to convert
        
    Returns:
        CrewAI tool
    """
    try:
        # Import CrewAI components
        from crewai.tools import Tool as CrewAITool
    except ImportError:
        logger.error("CrewAI not installed. Please install crewai to use this feature.")
        raise ImportError("CrewAI not installed. Please install crewai to use this feature.")
    
    logger.info(f"Converting Contexa tool {tool.name} to CrewAI format")
    
    # Define the function that will be executed by the CrewAI tool
    def execute_contexa_tool(input_str: str) -> str:
        """Execute the Contexa tool with the given input."""
        try:
            # Parse the input
            if isinstance(input_str, str):
                try:
                    # Try to parse as JSON first
                    params = json.loads(input_str)
                except json.JSONDecodeError:
                    # If not valid JSON, use as a single parameter if tool expects it
                    first_param = next(iter(tool.parameters.keys()), None)
                    if first_param:
                        params = {first_param: input_str}
                    else:
                        params = {}
            elif isinstance(input_str, dict):
                params = input_str
            else:
                params = {}
            
            # Run the Contexa tool
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(tool(**params))
            
            # Return the result as a string
            if hasattr(result, "result"):
                return result.result
            return str(result)
        except Exception as e:
            logger.error(f"Error executing Contexa tool {tool.name}: {str(e)}")
            return f"Error: {str(e)}"
    
    # Create the CrewAI tool
    crewai_tool = CrewAITool(
        name=tool.name,
        description=tool.description,
        func=execute_contexa_tool,
    )
    
    return crewai_tool


@trace(kind=SpanKind.INTERNAL)
async def convert_model_to_crewai(model: ContexaModel) -> Any:
    """Convert a Contexa model to CrewAI format.
    
    Args:
        model: The Contexa model to convert
        
    Returns:
        CrewAI LLM
    """
    try:
        # Import CrewAI components
        from crewai.llms.base import LLM as CrewAILLM
    except ImportError:
        logger.error("CrewAI not installed. Please install crewai to use this feature.")
        raise ImportError("CrewAI not installed. Please install crewai to use this feature.")
    
    logger.info(f"Converting Contexa model {model.model_name} to CrewAI format")
    
    # Create a class that adapts the Contexa model to the CrewAI LLM interface
    class ContexaCrewAIModel(CrewAILLM):
        """CrewAI wrapper for a Contexa model."""
        
        def __init__(self, contexa_model: ContexaModel):
            """Initialize with a Contexa model."""
            self.contexa_model = contexa_model
            self.model_name = contexa_model.model_name
            self.provider = contexa_model.provider
        
        @property
        def _llm_type(self) -> str:
            """Return the type of this LLM."""
            return f"contexa-{self.provider}"
        
        async def _agenerate(self, prompt: str, **kwargs) -> str:
            """Generate a response asynchronously."""
            # Create a message for the model
            messages = [ModelMessage(role="user", content=prompt)]
            
            # Generate a response
            response = await self.contexa_model.generate(messages)
            
            # Return the response content
            return response.content
        
        def generate(self, prompt: str, **kwargs) -> str:
            """Generate a response synchronously."""
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._agenerate(prompt, **kwargs))
    
    # Create and return the CrewAI model
    crewai_model = ContexaCrewAIModel(model)
    return crewai_model


@trace(kind=SpanKind.INTERNAL)
async def convert_agent_to_crewai(agent: Union[ContexaAgent, RemoteAgent]) -> Any:
    """Convert a Contexa agent to CrewAI format.
    
    Args:
        agent: The Contexa agent to convert
        
    Returns:
        CrewAI agent
    """
    try:
        # Import CrewAI components
        from crewai.agent import Agent as CrewAIAgent
    except ImportError:
        logger.error("CrewAI not installed. Please install crewai to use this feature.")
        raise ImportError("CrewAI not installed. Please install crewai to use this feature.")
    
    logger.info(f"Converting Contexa agent {agent.name} to CrewAI format")
    
    # Define the function that will be executed by the CrewAI agent
    def execute_contexa_agent(task: str) -> str:
        """Execute the Contexa agent with the given task."""
        try:
            # Run the Contexa agent
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(agent.run(task))
            
            # Return the result as a string
            return str(result)
        except Exception as e:
            logger.error(f"Error executing Contexa agent {agent.name}: {str(e)}")
            return f"Error: {str(e)}"
    
    # Create the CrewAI agent
    crewai_agent = CrewAIAgent(
        name=agent.name,
        description=agent.description,
        goal="Execute tasks passed to it using the underlying Contexa agent.",
        backstory=f"An agent powered by Contexa SDK, originally named {agent.name}.",
        # CrewAI needs a model, but we'll use it minimally since we're delegating to Contexa
        # We'll need to provide a default model when actually using this
        verbose=True,
        allow_delegation=False,  # Delegation is handled by Contexa
    )
    
    # Attach a custom method to handle tasks
    crewai_agent._contexa_execute = execute_contexa_agent
    
    # Override the execute method to use our custom handler
    original_execute = crewai_agent.execute
    
    def wrapped_execute(task, *args, **kwargs):
        # If it's a simple string task, use our Contexa handler
        if isinstance(task, str):
            return execute_contexa_agent(task)
        # Otherwise, fall back to the original execute method
        return original_execute(task, *args, **kwargs)
    
    crewai_agent.execute = wrapped_execute
    
    return crewai_agent


@trace(kind=SpanKind.INTERNAL)
async def adapt_crewai_agent(crewai_agent: Any) -> RemoteAgent:
    """Adapt a CrewAI agent to work with Contexa.
    
    Args:
        crewai_agent: The CrewAI agent to adapt
        
    Returns:
        Contexa RemoteAgent that wraps the CrewAI agent
    """
    # Create a wrapper that executes the CrewAI agent
    class CrewAIAgentWrapper(RemoteAgent):
        """Wrapper for a CrewAI agent."""
        
        def __init__(self, crewai_agent: Any):
            """Initialize with a CrewAI agent."""
            super().__init__(
                endpoint_url="crewai://agent",  # Dummy endpoint
                name=getattr(crewai_agent, "name", "CrewAI Agent"),
                description=getattr(crewai_agent, "description", ""),
            )
            self.crewai_agent = crewai_agent
        
        async def run(self, query: str, **kwargs) -> str:
            """Run the CrewAI agent."""
            try:
                # Execute the CrewAI agent
                # CrewAI primarily uses synchronous code
                if hasattr(self.crewai_agent, "execute"):
                    result = self.crewai_agent.execute(query)
                else:
                    # If no execute method, try run
                    result = self.crewai_agent.run(query)
                
                return str(result)
            except Exception as e:
                logger.error(f"Error running CrewAI agent: {str(e)}")
                raise
    
    # Create and return the wrapper
    return CrewAIAgentWrapper(crewai_agent) 