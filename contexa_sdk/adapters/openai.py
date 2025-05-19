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

# Import thread management
from contexa_sdk.adapters.openai.thread import (
    get_thread_for_agent,
    memory_to_thread,
    thread_to_memory,
    handoff_to_thread,
)


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
            from openai_agents import function_tool
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
            A dictionary containing the model configuration with keys:
            - model_name: The model name
            - config: Additional configuration
            - provider: The model provider
        """
        # For OpenAI Agents SDK, we'll provide a standardized model info dictionary
        try:
            from openai import OpenAI
        except ImportError:
            pass  # Allow this to fail silently for environments without OpenAI
            
        # Attempt to create an OpenAI client if the API key is available
        client = None
        if model.config.get("api_key"):
            try:
                client = OpenAI(api_key=model.config.get("api_key"))
            except Exception:
                # If client creation fails, we'll fall back to returning just the model name
                pass
                
        return {
            "client": client,
            "model_name": model.model_name,
            "config": model.config,
            "provider": model.provider,
        }
        
    def agent(self, agent: ContexaAgent) -> Any:
        """Convert a Contexa agent to an OpenAI Agents SDK agent.
        
        Args:
            agent: The Contexa agent to convert
            
        Returns:
            An OpenAI Agents SDK Agent object
        """
        try:
            from openai_agents import Agent
        except ImportError:
            raise ImportError(
                "OpenAI Agents SDK not found. Install with `pip install contexa-sdk[openai]`."
            )
            
        # Convert the tools
        openai_tools = [self.tool(tool) for tool in agent.tools]
        
        # Convert the model
        model_info = self.model(agent.model)
        model_name = model_info["model_name"]
        
        # Create the OpenAI agent
        openai_agent = Agent(
            name=agent.name,
            instructions=agent.system_prompt,
            tools=openai_tools,
            model=model_name,
        )
        
        # Store the original Contexa agent for reference and handoff support
        openai_agent.__contexa_agent__ = agent
        
        # Create a thread for this agent and store the conversation history
        thread_id = memory_to_thread(agent)
        openai_agent.__thread_id__ = thread_id
        
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
            from openai_agents import Agent, Runner
            from openai import OpenAI
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
        
        # Check if we need to use the Assistants API or the Agents SDK
        # If the target agent has an assistant_id (from Assistants API), use threads
        assistant_id = getattr(target_agent, "assistant_id", None)
        if assistant_id:
            # Use thread-based handoff for Assistants API
            response = handoff_to_thread(handoff_data, assistant_id)
        else:
            # Modify the handoff query to include context for Agents SDK
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
    
    async def adapt_openai_assistant(
        self, 
        assistant_id: str, 
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> ContexaAgent:
        """Adapt an OpenAI Assistant to a Contexa agent.
        
        Args:
            assistant_id: The OpenAI Assistant ID
            name: Optional name override
            description: Optional description override
            
        Returns:
            A Contexa agent that wraps the OpenAI Assistant
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI Python SDK not found. Install with `pip install openai`.")
        
        # Create a client
        client = OpenAI()
        
        # Retrieve the assistant
        assistant = client.beta.assistants.retrieve(assistant_id)
        
        # Extract the tools
        tool_list = []
        for tool in assistant.tools:
            if tool.type == "function":
                # Create a Contexa tool from the function definition
                @ContexaTool.register(
                    name=tool.function.name, 
                    description=tool.function.description or ""
                )
                async def function_tool(**kwargs):
                    # This is a placeholder - the actual function call would happen
                    # through the Assistant API when the assistant is run
                    return f"Function {tool.function.name} called with {kwargs}"
                
                tool_list.append(function_tool)
        
        # Create a Contexa model
        model = ContexaModel(
            provider="openai",
            model_name=assistant.model,
        )
        
        # Create a Contexa agent
        agent = ContexaAgent(
            name=name or assistant.name,
            description=description or getattr(assistant, "description", ""),
            model=model,
            tools=tool_list,
            system_prompt=assistant.instructions,
        )
        
        # Store the OpenAI assistant ID
        agent.metadata = {
            "assistant_id": assistant_id,
            "assistant_created_at": getattr(assistant, "created_at", None),
        }
        
        return agent


# Create a singleton instance
_adapter = OpenAIAdapter()

# Expose the adapter methods at the module level
tool = _adapter.tool
model = _adapter.model
agent = _adapter.agent
prompt = _adapter.prompt
adapt_assistant = _adapter.adapt_openai_assistant

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