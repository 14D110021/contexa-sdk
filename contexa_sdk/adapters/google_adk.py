"""Google ADK adapter for converting Contexa objects to Google ADK objects."""

import inspect
import asyncio
import json
from typing import Any, Dict, List, Optional, Union, Callable

from contexa_sdk.adapters.base import BaseAdapter
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel, ModelMessage
from contexa_sdk.core.agent import ContexaAgent, HandoffData
from contexa_sdk.core.prompt import ContexaPrompt


class GoogleADKAdapter(BaseAdapter):
    """Google ADK adapter for converting Contexa objects to Google ADK objects."""
    
    def tool(self, tool: ContexaTool) -> Any:
        """Convert a Contexa tool to a Google ADK tool.
        
        Args:
            tool: The Contexa tool to convert
            
        Returns:
            A Google ADK Tool object
        """
        try:
            from adk import Tool
        except ImportError:
            raise ImportError(
                "Google ADK not found. Install with `pip install contexa-sdk[google-adk]`."
            )
            
        # Create a sync wrapper function for our async tool
        def sync_tool_fn(**kwargs):
            return asyncio.run(tool(**kwargs))
            
        # Create the Google ADK tool
        return Tool.from_function(
            function=sync_tool_fn,
            name=tool.name,
            description=tool.description,
        )
        
    def model(self, model: ContexaModel) -> Any:
        """Convert a Contexa model to a Google ADK model.
        
        Args:
            model: The Contexa model to convert
            
        Returns:
            A Google ADK Model object
        """
        try:
            from adk import GeminiModel
        except ImportError:
            raise ImportError(
                "Google ADK not found. Install with `pip install contexa-sdk[google-adk]`."
            )
            
        # If it's a Google model, create a GeminiModel instance
        if model.provider == "google":
            return GeminiModel(
                model_name=model.model_name,
                api_key=model.config.api_key,
            )
        else:
            # For non-Google models, create a custom wrapper
            # This is a simplified example and may need more work
            # to properly integrate with Google ADK
            from adk.core import Model
            
            class ContexaModelWrapper(Model):
                def __init__(self, contexa_model):
                    self.contexa_model = contexa_model
                    
                def generate(self, prompt, **kwargs):
                    message = ModelMessage(role="user", content=prompt)
                    response = asyncio.run(
                        self.contexa_model.generate([message])
                    )
                    return response.content
                    
            return ContexaModelWrapper(model)
            
    def agent(self, agent: ContexaAgent) -> Any:
        """Convert a Contexa agent to a Google ADK agent.
        
        Args:
            agent: The Contexa agent to convert
            
        Returns:
            A Google ADK Agent object
        """
        try:
            from adk import Agent
        except ImportError:
            raise ImportError(
                "Google ADK not found. Install with `pip install contexa-sdk[google-adk]`."
            )
            
        # Convert the model
        adk_model = self.model(agent.model)
        
        # Convert the tools
        adk_tools = [self.tool(tool) for tool in agent.tools]
        
        # Create the Google ADK agent
        adk_agent = Agent(
            model=adk_model,
            tools=adk_tools,
            system_prompt=agent.system_prompt,
            name=agent.name,
        )
        
        # Store the original Contexa agent for reference and handoff support
        adk_agent.__contexa_agent__ = agent
        
        return adk_agent
        
    def prompt(self, prompt: ContexaPrompt) -> Any:
        """Convert a Contexa prompt to a format usable by Google ADK.
        
        Args:
            prompt: The Contexa prompt to convert
            
        Returns:
            A string template usable by Google ADK
        """
        # Google ADK typically uses string templates
        return prompt.template
    
    async def handoff_to_google_adk_agent(
        self,
        source_agent: ContexaAgent,
        target_agent: Any,  # Google ADK Agent object
        query: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Handle handoff to a Google ADK agent.
        
        Args:
            source_agent: The Contexa agent handing off the task
            target_agent: The Google ADK Agent to hand off to
            query: The query to send to the target agent
            context: Additional context to pass to the target agent
            metadata: Additional metadata for the handoff
            
        Returns:
            The target agent's response
        """
        try:
            from adk import Agent
        except ImportError:
            raise ImportError(
                "Google ADK not found. Install with `pip install contexa-sdk[google-adk]`."
            )
            
        if not isinstance(target_agent, Agent):
            raise TypeError("target_agent must be a Google ADK Agent object")
            
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
        
        # Google ADK has different ways to handle system prompts, so we'll modify the query
        # to include the handoff context instead
        context_str = json.dumps(handoff_data.context, indent=2)
        enhanced_query = (
            f"[Task handoff from agent '{source_agent.name}']\n\n"
            f"CONTEXT: {context_str}\n\n"
            f"TASK: {query}"
        )
        
        # Run the target agent with the enhanced query
        response = await asyncio.to_thread(target_agent.generate, enhanced_query)
        
        # Update the handoff data with the result
        handoff_data.result = response
        
        # Update the Contexa agent associated with the Google ADK agent if it exists
        if hasattr(target_agent, "__contexa_agent__"):
            target_contexa_agent = target_agent.__contexa_agent__
            target_contexa_agent.receive_handoff(handoff_data)
            
        return response


# Create a singleton instance
_adapter = GoogleADKAdapter()

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
    """Handle handoff from a Contexa agent to a Google ADK agent."""
    return await _adapter.handoff_to_google_adk_agent(
        source_agent=source_agent,
        target_agent=target_agent,
        query=query,
        context=context,
        metadata=metadata,
    ) 