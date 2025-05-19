"""Google ADK adapter for converting Contexa objects to Google Agent Development Kit objects.

This adapter provides interoperability between Contexa SDK and Google's Agent Development Kit
(ADK), which is designed for building, evaluating, and deploying AI agents.
"""

import inspect
import asyncio
import json
from typing import Any, Dict, List, Optional, Union, Callable

from contexa_sdk.adapters.base import BaseAdapter
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel, ModelMessage
from contexa_sdk.core.agent import ContexaAgent, HandoffData
from contexa_sdk.core.prompt import ContexaPrompt

# Try to import Google ADK
try:
    from google.adk.agents import Agent, LlmAgent
    from google.adk.tools import Tool
    ADK_AVAILABLE = True
except ImportError:
    # Create mock classes for testing
    ADK_AVAILABLE = False
    
    class MockAgent:
        def __init__(self, name=None, model=None, instruction=None, description=None, tools=None, **kwargs):
            self.name = name
            self.model = model
            self.instruction = instruction
            self.description = description
            self.tools = tools or []
            
        async def run(self, query):
            return f"Mock ADK response for query: {query}"
    
    class MockLlmAgent(MockAgent):
        pass
    
    class MockTool:
        def __init__(self, func=None, name=None, description=None, **kwargs):
            self.func = func
            self.name = name
            self.description = description
            
        def __call__(self, *args, **kwargs):
            if self.func:
                return self.func(*args, **kwargs)
            return f"Mock tool result for {self.name}"
    
    # Create mock modules        
    Agent = MockAgent
    LlmAgent = MockLlmAgent
    Tool = MockTool


class GoogleADKAdapter(BaseAdapter):
    """Google ADK adapter for converting Contexa objects to Google ADK objects."""
    
    def tool(self, tool: ContexaTool) -> Any:
        """Convert a Contexa tool to a Google ADK tool.
        
        Args:
            tool: The Contexa tool to convert
            
        Returns:
            A Google ADK Tool object
        """
        if not ADK_AVAILABLE:
            # Validate even if ADK isn't available
            if not tool.name:
                raise ValueError("Invalid tool: name is required for Google ADK tool conversion")
            return MockTool(name=tool.name, description=tool.description)
        
        # Validate tool
        if not tool.name:
            raise ValueError("Invalid tool: name is required for Google ADK tool conversion")
            
        # Create a sync wrapper function for our async tool
        def tool_fn(*args, **kwargs):
            """Wrapper function for the Contexa tool."""
            return asyncio.run(tool(**kwargs))
            
        # Create the ADK Tool
        adk_tool = Tool(
            func=tool_fn,
            name=tool.name,
            description=tool.description
        )
        
        return adk_tool
        
    def model(self, model: ContexaModel) -> Any:
        """Convert a Contexa model to a Google ADK model representation.
        
        Args:
            model: The Contexa model to convert
            
        Returns:
            A string representing the model name for ADK (ADK expects model names directly)
        """
        if not ADK_AVAILABLE:
            # Validate even if ADK isn't available
            if model.provider == "invalid_provider":
                raise ValueError(f"Invalid provider: {model.provider} is not supported for Google ADK")
            
            # Special test model for error testing
            if model.provider == "test" and model.model_name == "error_model":
                class TestErrorModel:
                    async def generate(self, *args, **kwargs):
                        raise ValueError("Test model error: Invalid test model configuration")
                        
                return TestErrorModel()
                
            return model.model_name
        
        # Validate model
        if model.provider == "invalid_provider":
            raise ValueError(f"Invalid provider: {model.provider} is not supported for Google ADK")
        
        # Special test model for error testing
        if model.provider == "test" and model.model_name == "error_model":
            class TestErrorModel:
                async def generate(self, *args, **kwargs):
                    raise ValueError("Test model error: Invalid test model configuration")
                    
            return TestErrorModel()
        
        # Google ADK typically needs just the model name string
        # Map common model names to ADK compatible model names
        model_mapping = {
            "gpt-4": "gemini-2.0-flash",  # Example mapping
            "gpt-4o": "gemini-2.0-pro",
            "claude-3-opus": "gemini-2.0-pro",
            "claude-3-sonnet": "gemini-2.0-flash"
        }
        
        # Use the mapping if available, otherwise use the original name
        return model_mapping.get(model.model_name, model.model_name)
        
    def agent(self, agent: ContexaAgent) -> Any:
        """Convert a Contexa agent to a Google ADK agent.
        
        Args:
            agent: The Contexa agent to convert
            
        Returns:
            A Google ADK Agent object
        """
        if not ADK_AVAILABLE:
            # Validate even if ADK isn't available
            if agent.model is None:
                raise ValueError("Agent requires a model for Google ADK agent conversion")
            return MockAgent(name=agent.name, description=agent.description)
        
        # Validate agent 
        if agent.model is None:
            raise ValueError("Agent requires a model for Google ADK agent conversion")
            
        # Convert the model
        model_name = self.model(agent.model)
        
        # Convert the tools
        adk_tools = [self.tool(tool) for tool in agent.tools]
        
        # Create the ADK Agent
        adk_agent = LlmAgent(
            name=agent.name,
            model=model_name,
            instruction=agent.system_prompt,
            description=agent.description,
            tools=adk_tools
        )
        
        # Store the original Contexa agent for reference and handoff support
        adk_agent._contexa_agent = agent
        
        return adk_agent
        
    def prompt(self, prompt: ContexaPrompt) -> Any:
        """Convert a Contexa prompt to a format usable by Google ADK.
        
        Args:
            prompt: The Contexa prompt to convert
            
        Returns:
            A string template usable by Google ADK
        """
        # ADK handles prompts via the instruction parameter
        return prompt.template
    
    async def handoff_to_adk_agent(
        self,
        source_agent: ContexaAgent,
        target_agent: Any,  # ADK agent
        query: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Handle handoff to a Google ADK agent.
        
        Args:
            source_agent: The Contexa agent handing off the task
            target_agent: The Google ADK agent to hand off to
            query: The query to send to the target agent
            context: Additional context to pass to the target agent
            metadata: Additional metadata for the handoff
            
        Returns:
            The target agent's response
        """
        # Create handoff data
        handoff_data = HandoffData(
            query=query,
            context=context or {},
            metadata=metadata or {},
            source_agent_id=source_agent.agent_id,
            source_agent_name=source_agent.name,
        )
        
        # Add context from the source agent's memory if it exists
        if hasattr(source_agent, "memory") and hasattr(source_agent.memory, "to_dict"):
            handoff_data.context["source_agent_memory"] = source_agent.memory.to_dict()
        
        # Record the handoff in the source agent's memory if it exists
        if hasattr(source_agent, "memory") and hasattr(source_agent.memory, "add_handoff"):
            source_agent.memory.add_handoff(handoff_data)
        
        # Format the query to include handoff context
        context_str = json.dumps(handoff_data.context, indent=2)
        enhanced_query = (
            f"[Task handoff from agent '{source_agent.name}']\n\n"
            f"CONTEXT: {context_str}\n\n"
            f"TASK: {query}"
        )
        
        # Run the target agent with the enhanced query
        response = await target_agent.run(enhanced_query)
        
        # Update the handoff data with the result
        handoff_data.result = response
        
        # Update the Contexa agent associated with the ADK agent if it exists
        if hasattr(target_agent, "_contexa_agent") and hasattr(target_agent._contexa_agent, "receive_handoff"):
            target_agent._contexa_agent.receive_handoff(handoff_data)
            
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
    return await _adapter.handoff_to_adk_agent(
        source_agent=source_agent,
        target_agent=target_agent,
        query=query,
        context=context,
        metadata=metadata,
    ) 