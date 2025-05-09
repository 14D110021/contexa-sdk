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
            An OpenAI Agents SDK Tool object
        """
        try:
            from openai_agents import Tool
        except ImportError:
            raise ImportError(
                "OpenAI Agents SDK not found. Install with `pip install contexa-sdk[openai]`."
            )
            
        # Get the tool schema for OpenAI
        schema = tool.schema.model_json_schema()
        
        # Create an async function that will call our tool
        async def tool_function(**kwargs):
            return await tool(**kwargs)
            
        # Create the OpenAI Agent SDK tool
        return Tool.from_function(
            function=tool_function,
            name=tool.name,
            description=tool.description,
            schema=schema,
        )
        
    def model(self, model: ContexaModel) -> Any:
        """Convert a Contexa model to an OpenAI model.
        
        Args:
            model: The Contexa model to convert
            
        Returns:
            An OpenAI model name/identifier (str)
        """
        # For OpenAI, we just need the model name
        # Typically use OpenAI models directly with this adapter
        return model.model_name
        
    def agent(self, agent: ContexaAgent) -> Any:
        """Convert a Contexa agent to an OpenAI Agents SDK agent.
        
        Args:
            agent: The Contexa agent to convert
            
        Returns:
            An OpenAI Agents SDK Agent object
        """
        try:
            from openai_agents import Agent, OpenAIModel
        except ImportError:
            raise ImportError(
                "OpenAI Agents SDK not found. Install with `pip install contexa-sdk[openai]`."
            )
            
        # Convert the model
        # OpenAI Agent SDK expects an OpenAI model name
        openai_model = OpenAIModel(
            model=self.model(agent.model),
            api_key=agent.config.api_key,
        )
        
        # Convert the tools
        openai_tools = [self.tool(tool) for tool in agent.tools]
        
        # Create the OpenAI agent
        openai_agent = Agent(
            model=openai_model,
            tools=openai_tools,
            system_prompt=agent.system_prompt,
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
        
        The OpenAI Agents SDK doesn't have built-in handoff functionality,
        but we can emulate it by adding context to the system prompt.
        
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
            from openai_agents import Agent
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
        
        # Modify the system prompt to include handoff context
        original_prompt = target_agent.system_prompt
        context_str = json.dumps(handoff_data.context, indent=2)
        handoff_prompt = (
            f"{original_prompt}\n\n"
            f"IMPORTANT: This is a task handoff from agent '{source_agent.name}' "
            f"(ID: {source_agent.agent_id}).\n"
            f"Handoff context: {context_str}"
        )
        
        # Update the agent with the new prompt
        target_agent.system_prompt = handoff_prompt
        
        # Run the target agent with the query
        response = await target_agent.run(query)
        
        # Reset the system prompt back to the original
        target_agent.system_prompt = original_prompt
        
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