"""OpenAI adapter for converting Contexa objects to OpenAI Agents SDK objects."""

import inspect
import asyncio
import json
from typing import Any, Dict, List, Optional, Union, Callable

from contexa_sdk.adapters.base import BaseAdapter
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel, ModelMessage
from contexa_sdk.core.agent import ContexaAgent, HandoffData
from contexa_sdk.core.prompt import ContexaPrompt


class OpenAIAdapter(BaseAdapter):
    """OpenAI adapter for converting Contexa objects to OpenAI Agents SDK objects."""
    
    def tool(self, tool: ContexaTool) -> Any:
        """Convert a Contexa tool to an OpenAI Agents SDK tool.
        
        Args:
            tool: The Contexa tool to convert
            
        Returns:
            An OpenAI Agents SDK function_tool
        """
        try:
            from agents import function_tool
        except ImportError:
            raise ImportError(
                "OpenAI Agents SDK not found. Install with `pip install contexa-sdk[openai]`."
            )
            
        # Create a wrapper function that will call our tool
        @function_tool
        async def contexa_tool(**kwargs):
            """Tool description from Contexa."""
            return await tool(**kwargs)
            
        # Update the tool metadata to match the original Contexa tool
        contexa_tool.__name__ = tool.name
        contexa_tool.__doc__ = tool.description
        
        return contexa_tool
        
    def model(self, model: ContexaModel) -> Any:
        """Convert a Contexa model to an OpenAI model.
        
        Args:
            model: The Contexa model to convert
            
        Returns:
            A model string identifier compatible with OpenAI Agents SDK
        """
        # For OpenAI Agents SDK, we just need the model name
        # Can be either an OpenAI model name or a supported model via LiteLLM
        return model.model_name
        
    def agent(self, agent: ContexaAgent) -> Any:
        """Convert a Contexa agent to an OpenAI Agents SDK agent.
        
        Args:
            agent: The Contexa agent to convert
            
        Returns:
            An OpenAI Agents SDK Agent object
        """
        try:
            from agents import Agent
        except ImportError:
            raise ImportError(
                "OpenAI Agents SDK not found. Install with `pip install contexa-sdk[openai]`."
            )
            
        # Convert the tools
        openai_tools = [self.tool(tool) for tool in agent.tools]
        
        # Create the OpenAI agent
        openai_agent = Agent(
            name=agent.name,
            instructions=agent.system_prompt,
            tools=openai_tools,
            model=self.model(agent.model),
        )
        
        # Store the original Contexa agent for reference and handoff support
        openai_agent.__contexa_agent__ = agent
        
        return openai_agent
        
    def prompt(self, prompt: ContexaPrompt) -> Any:
        """Convert a Contexa prompt to a format usable by OpenAI Agents SDK.
        
        Args:
            prompt: The Contexa prompt to convert
            
        Returns:
            A string template usable by OpenAI Agents SDK
        """
        # OpenAI Agents SDK typically just uses string templates
        return prompt.template
    
    async def handoff_to_openai_agent(
        self,
        source_agent: ContexaAgent,
        target_agent: Any,  # OpenAI Agents SDK Agent object
        query: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Handle handoff to an OpenAI agent.
        
        The OpenAI Agents SDK has built-in handoff functionality now,
        but we'll use our approach to maintain consistency.
        
        Args:
            source_agent: The Contexa agent handing off the task
            target_agent: The OpenAI Agent to hand off to
            query: The query to send to the target agent
            context: Additional context to pass to the target agent
            metadata: Additional metadata for the handoff
            
        Returns:
            The target agent's response
        """
        try:
            from agents import Agent, Runner
        except ImportError:
            raise ImportError(
                "OpenAI Agents SDK not found. Install with `pip install contexa-sdk[openai]`."
            )
            
        if not isinstance(target_agent, Agent):
            raise TypeError("target_agent must be an OpenAI Agents SDK Agent object")
            
        # Create handoff data
        handoff_data = HandoffData(
            query=query,
            context=context or {},
            metadata=metadata or {},
            source_agent_id=source_agent.agent_id,
            source_agent_name=source_agent.name,
        )
        
        # Add context from the source agent's memory
        handoff_data.context["source_agent_memory"] = source_agent.memory.to_dict()
        
        # Record the handoff in the source agent's memory
        source_agent.memory.add_handoff(handoff_data)
        
        # Modify the handoff query to include context
        context_str = json.dumps(handoff_data.context, indent=2)
        enhanced_query = (
            f"[Task handoff from agent '{source_agent.name}']\n\n"
            f"CONTEXT: {context_str}\n\n"
            f"TASK: {query}"
        )
        
        # Run the target agent with the enhanced query using the Runner
        result = await Runner.run(target_agent, enhanced_query)
        
        # Extract the final output from the result
        response = str(result.final_output)
        
        # Update the handoff data with the result
        handoff_data.result = response
        
        # Update the Contexa agent associated with the OpenAI agent if it exists
        if hasattr(target_agent, "__contexa_agent__"):
            target_contexa_agent = target_agent.__contexa_agent__
            target_contexa_agent.receive_handoff(handoff_data)
            
        return response


# Create a singleton instance
_adapter = OpenAIAdapter()

# Expose the adapter methods at the module level
tool = _adapter.tool
model = _adapter.model
agent = _adapter.agent
prompt = _adapter.prompt

# Expose handoff method at the module level
async def handoff(
    source_agent: ContexaAgent,
    target_agent: Any,
    query: str,
    context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Handle handoff from a Contexa agent to an OpenAI agent."""
    return await _adapter.handoff_to_openai_agent(
        source_agent=source_agent,
        target_agent=target_agent,
        query=query,
        context=context,
        metadata=metadata,
    ) 