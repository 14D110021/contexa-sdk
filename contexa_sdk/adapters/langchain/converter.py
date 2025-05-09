"""Converters for LangChain integration."""

import inspect
import json
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, cast

from contexa_sdk.core.tool import BaseTool, RemoteTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent, RemoteAgent
from contexa_sdk.observability import get_logger, trace, SpanKind

# Create a logger for this module
logger = get_logger(__name__)


@trace(kind=SpanKind.INTERNAL)
async def convert_tool_to_langchain(tool: Union[BaseTool, RemoteTool]) -> Any:
    """Convert a Contexa tool to LangChain format.
    
    Args:
        tool: The tool to convert
        
    Returns:
        LangChain tool
    """
    try:
        # Import LangChain components
        from langchain.tools import BaseTool as LangChainBaseTool
        from langchain.tools import StructuredTool
        from pydantic import BaseModel, create_model
    except ImportError:
        logger.error("LangChain not installed. Please install langchain to use this feature.")
        raise ImportError("LangChain not installed. Please install langchain to use this feature.")
    
    logger.info(f"Converting Contexa tool {tool.name} to LangChain format")
    
    # Create a Pydantic model for the tool parameters
    param_fields = {}
    for name, schema in tool.parameters.items():
        param_type = str  # Default type
        
        # Map parameter types to Python types
        type_map = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        
        if "type" in schema:
            param_type = type_map.get(schema["type"], str)
        
        # Add to fields with appropriate default if not required
        if schema.get("required", False):
            param_fields[name] = (param_type, ...)
        else:
            param_fields[name] = (Optional[param_type], None)
    
    # Create the Pydantic model for the tool
    ToolParameters = create_model(
        f"{tool.name.title()}Parameters",
        **param_fields
    )
    
    # Define the run function for the tool
    async def _run(params: ToolParameters) -> str:
        try:
            # Convert Pydantic model to dict
            params_dict = params.dict() if hasattr(params, "dict") else params
            
            # Remove None values which are optional parameters
            params_dict = {k: v for k, v in params_dict.items() if v is not None}
            
            # Call the Contexa tool
            result = await tool(**params_dict)
            
            # Return the result as a string
            if hasattr(result, "result"):
                return result.result
            return str(result)
        except Exception as e:
            logger.error(f"Error running tool {tool.name}: {str(e)}")
            return f"Error: {str(e)}"
    
    # Define a synchronous run if needed
    def _run_sync(params: ToolParameters) -> str:
        """Synchronous wrapper for async tool execution."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_run(params))
    
    # Create the LangChain tool
    langchain_tool = StructuredTool.from_function(
        func=_run_sync,
        name=tool.name,
        description=tool.description,
        args_schema=ToolParameters,
        return_direct=False,
        coroutine=_run,
    )
    
    return langchain_tool


@trace(kind=SpanKind.INTERNAL)
async def convert_model_to_langchain(model: ContexaModel) -> Any:
    """Convert a Contexa model to LangChain format.
    
    Args:
        model: The model to convert
        
    Returns:
        LangChain language model
    """
    try:
        # Import LangChain components
        from langchain.llms.base import BaseLLM
        from langchain.chat_models.base import BaseChatModel
    except ImportError:
        logger.error("LangChain not installed. Please install langchain to use this feature.")
        raise ImportError("LangChain not installed. Please install langchain to use this feature.")
    
    logger.info(f"Converting Contexa model {model.model_name} to LangChain format")
    
    # Try to determine the most appropriate LangChain model type based on the provider
    provider = model.provider.lower()
    
    # Define the wrapper class for the model
    class ContexaLangChainModel(BaseChatModel):
        """LangChain wrapper for a Contexa model."""
        
        def __init__(self, contexa_model: ContexaModel):
            """Initialize with a Contexa model."""
            super().__init__()
            self.contexa_model = contexa_model
            self.model_name = contexa_model.model_name
            self.provider = contexa_model.provider
        
        @property
        def _llm_type(self) -> str:
            """Return the type of this LLM."""
            return f"contexa-{self.provider}"
        
        @property
        def _identifying_params(self) -> Dict:
            """Return identifying parameters."""
            return {
                "model_name": self.model_name,
                "provider": self.provider,
            }
        
        async def _agenerate(self, messages, **kwargs):
            """Generate asynchronously."""
            from langchain.schema import (
                AIMessage, 
                HumanMessage, 
                SystemMessage, 
                ChatGeneration,
                ChatResult,
            )
            
            # Convert LangChain messages to Contexa format
            contexa_messages = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    role = "user"
                elif isinstance(msg, AIMessage):
                    role = "assistant"
                elif isinstance(msg, SystemMessage):
                    role = "system"
                else:
                    role = "user"
                
                from contexa_sdk.core.model import ModelMessage
                contexa_messages.append(ModelMessage(
                    role=role,
                    content=msg.content,
                ))
            
            # Generate response
            response = await self.contexa_model.generate(contexa_messages)
            
            # Convert back to LangChain format
            ai_message = AIMessage(content=response.content)
            chat_generation = ChatGeneration(message=ai_message)
            
            # Create and return the result
            result = ChatResult(generations=[chat_generation])
            return result
        
        def _generate(self, messages, **kwargs):
            """Generate synchronously."""
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._agenerate(messages, **kwargs))
    
    # Create and return the LangChain model
    langchain_model = ContexaLangChainModel(model)
    return langchain_model


@trace(kind=SpanKind.INTERNAL)
async def convert_agent_to_langchain(agent: Union[ContexaAgent, RemoteAgent]) -> Any:
    """Convert a Contexa agent to LangChain format.
    
    Args:
        agent: The agent to convert
        
    Returns:
        LangChain agent
    """
    try:
        # Import LangChain components
        from langchain.agents import AgentExecutor
        from langchain.agents.agent import Agent as LangChainAgent
    except ImportError:
        logger.error("LangChain not installed. Please install langchain to use this feature.")
        raise ImportError("LangChain not installed. Please install langchain to use this feature.")
    
    logger.info(f"Converting Contexa agent to LangChain format")
    
    # Define the wrapper class for the agent
    class ContexaLangChainAgent(LangChainAgent):
        """LangChain wrapper for a Contexa agent."""
        
        def __init__(self, contexa_agent: Union[ContexaAgent, RemoteAgent]):
            """Initialize with a Contexa agent."""
            self.contexa_agent = contexa_agent
            
        @property
        def _agent_type(self) -> str:
            """Return the type of this agent."""
            return "contexa-agent"
        
        async def _aplan(self, intermediate_steps, **kwargs) -> Union[Dict, str]:
            """Plan asynchronously."""
            # Combine all previous context from intermediate steps
            combined_query = kwargs.get("input", "")
            
            if intermediate_steps:
                combined_query += "\nPrevious steps:\n"
                for action, result in intermediate_steps:
                    tool_name = action.tool if hasattr(action, "tool") else "unknown"
                    combined_query += f"- Used {tool_name} and got result: {result}\n"
            
            # Run the Contexa agent
            response = await self.contexa_agent.run(combined_query)
            
            # Parse for potential tool use (LangChain expects this)
            # LangChain uses a specific format to determine tool calls
            if "Action:" in response and "Action Input:" in response:
                action_parts = response.split("Action:", 1)[1].split("Action Input:", 1)
                if len(action_parts) == 2:
                    tool = action_parts[0].strip()
                    tool_input = action_parts[1].strip()
                    return {"tool": tool, "tool_input": tool_input}
            
            # If no tool use is detected, return the response directly
            return response
        
        def plan(self, intermediate_steps, **kwargs) -> Union[Dict, str]:
            """Plan synchronously."""
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._aplan(intermediate_steps, **kwargs))
    
    # Create the LangChain agent
    langchain_agent = ContexaLangChainAgent(agent)
    
    # For a complete agent, we would create an AgentExecutor with tools
    # but for most use cases, the agent itself is sufficient
    
    return langchain_agent


@trace(kind=SpanKind.INTERNAL)
async def adapt_langchain_agent(langchain_agent: Any) -> RemoteAgent:
    """Adapt a LangChain agent to work with Contexa.
    
    Args:
        langchain_agent: The LangChain agent to adapt
        
    Returns:
        Contexa RemoteAgent that wraps the LangChain agent
    """
    # Create a wrapper that executes the LangChain agent
    class LangChainAgentWrapper(RemoteAgent):
        """Wrapper for a LangChain agent."""
        
        def __init__(self, langchain_agent: Any):
            """Initialize with a LangChain agent."""
            super().__init__(
                endpoint_url="langchain://agent",  # Dummy endpoint
                name=getattr(langchain_agent, "name", "LangChain Agent"),
                description=getattr(langchain_agent, "description", ""),
            )
            self.langchain_agent = langchain_agent
        
        async def run(self, query: str, **kwargs) -> str:
            """Run the LangChain agent."""
            try:
                # Check if we're dealing with an AgentExecutor
                if hasattr(self.langchain_agent, "run"):
                    # AgentExecutor has a run method
                    if asyncio.iscoroutinefunction(self.langchain_agent.run):
                        result = await self.langchain_agent.run(query, **kwargs)
                    else:
                        result = self.langchain_agent.run(query, **kwargs)
                else:
                    # Assume it's a basic agent that needs to be called
                    result = await self._run_agent(query, **kwargs)
                    
                return str(result)
            except Exception as e:
                logger.error(f"Error running LangChain agent: {str(e)}")
                raise
        
        async def _run_agent(self, query: str, **kwargs) -> str:
            """Run a basic LangChain agent (not an AgentExecutor)."""
            # This depends on the type of LangChain agent
            # For most agents, we'll need to:
            # 1. Get the agent's plan
            # 2. Execute any tools
            # 3. Repeat until done
            
            # For now, just try to call the most common methods
            if hasattr(self.langchain_agent, "plan"):
                if asyncio.iscoroutinefunction(self.langchain_agent.plan):
                    response = await self.langchain_agent.plan([], input=query)
                else:
                    response = self.langchain_agent.plan([], input=query)
                
                # Response might be a dict with tool instructions or a string
                if isinstance(response, dict) and "text" in response:
                    return response["text"]
                return str(response)
            
            # If we can't find a way to run it, raise an error
            raise ValueError("Unsupported LangChain agent type")
    
    # Create and return the wrapper
    return LangChainAgentWrapper(langchain_agent) 