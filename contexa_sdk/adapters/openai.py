"""OpenAI adapter for converting Contexa objects to OpenAI Agents SDK objects.

This adapter provides integration between Contexa SDK and OpenAI's Agents SDK, converting
Contexa tools, models, agents, and prompts to their OpenAI equivalents.

The OpenAI adapter enables seamless use of Contexa SDK components with OpenAI's
Agents SDK, including support for both the newer Agents SDK and the Assistants API.
It handles the conversion of tool schemas, function signatures, and agent configurations
to ensure compatibility.

Key features:
- Converting ContexaTool objects to OpenAI function_tool instances
- Adapting ContexaModel configurations to OpenAI models
- Creating OpenAI Agent instances from ContexaAgent objects
- Converting ContexaPrompt objects to OpenAI-compatible strings
- Handling handoffs between Contexa agents and OpenAI agents
- Supporting OpenAI Assistants API integration through threads

Usage:
    from contexa_sdk.adapters import openai
    
    # Convert a Contexa tool to an OpenAI tool
    oa_tool = openai.tool(my_contexa_tool)
    
    # Convert a Contexa agent to an OpenAI agent
    oa_agent = openai.agent(my_contexa_agent)
    
    # Run the OpenAI agent
    result = await oa_agent.execute("What's the weather in Paris?")

Requirements:
    This adapter requires OpenAI Agents SDK to be installed:
    `pip install contexa-sdk[openai]`
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

# Import thread management
from contexa_sdk.adapters.openai.thread import (
    get_thread_for_agent,
    memory_to_thread,
    thread_to_memory,
    handoff_to_thread,
)

# Adapter version
__adapter_version__ = "0.1.0"


class OpenAIAdapter(BaseAdapter):
    """OpenAI adapter for converting Contexa objects to OpenAI Agents SDK objects.
    
    This adapter implements the BaseAdapter interface for the OpenAI Agents SDK.
    It provides methods to convert Contexa SDK core objects (tools, models, agents, 
    and prompts) to their OpenAI equivalents, enabling seamless integration
    between Contexa and OpenAI's agent technologies.
    
    The adapter supports both the newer OpenAI Agents SDK and the Assistants API,
    handling conversions for both approaches. It manages thread-based conversation
    state and provides utilities for agent handoffs.
    
    Attributes:
        None
        
    Methods:
        tool: Convert a Contexa tool to an OpenAI function_tool
        model: Convert a Contexa model to an OpenAI model configuration
        agent: Convert a Contexa agent to an OpenAI Agent
        prompt: Convert a Contexa prompt to an OpenAI-compatible string
        handoff_to_openai_agent: Handle handoff to an OpenAI agent
        adapt_openai_assistant: Create a Contexa agent from an OpenAI Assistant
        adapt_openai_agent: Adapt an OpenAI Agents SDK Agent to a Contexa agent
    """
    
    def tool(self, tool: ContexaTool) -> Any:
        """Convert a Contexa tool to an OpenAI Agents SDK tool.
        
        This method takes a Contexa tool and converts it to an OpenAI function_tool
        that can be used with OpenAI's Agents SDK. It wraps the tool's functionality
        in an appropriate function_tool decorator and preserves metadata like name
        and description.
        
        Args:
            tool: The Contexa tool to convert. Can be either a ContexaTool instance
                 or a function decorated with ContexaTool.register.
            
        Returns:
            An OpenAI Agents SDK function_tool that can be used with OpenAI agents.
            
        Raises:
            ImportError: If OpenAI Agents SDK dependencies are not installed.
            TypeError: If the input is not a valid ContexaTool instance.
            
        Example:
            ```python
            from contexa_sdk.core.tool import ContexaTool
            from contexa_sdk.adapters import openai
            
            @ContexaTool.register(
                name="weather",
                description="Get weather information for a location"
            )
            async def get_weather(location: str) -> str:
                return f"Weather in {location} is sunny"
                
            # Convert to OpenAI tool
            oa_tool = openai.tool(get_weather)
            ```
        """
        try:
            from agents import function_tool
        except ImportError:
            raise ImportError(
                "OpenAI Agents SDK not found. Install with `pip install openai-agents`."
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
        """Convert a Contexa model to an OpenAI model configuration.
        
        This method adapts a Contexa model to an OpenAI model configuration by
        extracting relevant parameters and optionally creating an OpenAI client
        if API credentials are available.
        
        Args:
            model: The Contexa model to convert. This should be a ContexaModel instance
                  with provider, model_name, and other configuration attributes.
            
        Returns:
            A dictionary containing the model configuration with keys:
            - client: An OpenAI client instance (if API key is available)
            - model_name: The model name
            - config: Additional configuration
            - provider: The model provider
            
        Raises:
            No specific exceptions are raised, as this method is designed to
            gracefully handle missing dependencies.
            
        Example:
            ```python
            from contexa_sdk.core.model import ContexaModel
            from contexa_sdk.adapters import openai
            
            model = ContexaModel(
                provider="openai",
                model_name="gpt-4o",
                temperature=0.7,
                config={"api_key": "your-api-key"}
            )
                
            # Convert to OpenAI model configuration
            oa_model_info = openai.model(model)
            ```
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
        
        This method creates an OpenAI Agent from a Contexa agent, converting
        the agent's tools, model configuration, and instructions. It also sets up
        thread-based conversation management for the agent.
        
        Args:
            agent: The Contexa agent to convert. Should be a ContexaAgent instance with
                  model, tools, and other configuration attributes.
            
        Returns:
            An OpenAI Agents SDK Agent object that can be used to run queries and tasks.
            The agent has __contexa_agent__ and __thread_id__ attributes for reference
            and state management.
            
        Raises:
            ImportError: If OpenAI Agents SDK dependencies are not installed.
            
        Example:
            ```python
            from contexa_sdk.core.agent import ContexaAgent
            from contexa_sdk.core.model import ContexaModel
            from contexa_sdk.adapters import openai
            
            agent = ContexaAgent(
                name="Assistant",
                model=ContexaModel(provider="openai", model_name="gpt-4o"),
                tools=[weather_tool, search_tool],
                system_prompt="You are a helpful assistant."
            )
                
            # Convert to OpenAI agent
            oa_agent = openai.agent(agent)
            result = await oa_agent.execute("What's the weather in Paris?")
            ```
        """
        try:
            from agents import Agent
        except ImportError:
            raise ImportError(
                "OpenAI Agents SDK not found. Install with `pip install openai-agents`."
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
        
        This method converts a Contexa prompt template to a string format that
        can be used with OpenAI Agents SDK. For OpenAI, this is typically just
        the raw template string.
        
        Args:
            prompt: The Contexa prompt to convert. Should be a ContexaPrompt instance
                   with a template attribute.
            
        Returns:
            A string template usable by OpenAI Agents SDK.
            
        Example:
            ```python
            from contexa_sdk.core.prompt import ContexaPrompt
            from contexa_sdk.adapters import openai
            
            prompt = ContexaPrompt(
                template="You are an assistant that helps with {task}."
            )
                
            # Convert to OpenAI-compatible string
            oa_prompt = openai.prompt(prompt)
            ```
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
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI Agents SDK not found. Install with `pip install openai-agents`."
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

    async def adapt_openai_agent(
        self, 
        openai_agent: Any,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> ContexaAgent:
        """Adapt an OpenAI Agents SDK Agent to a Contexa agent.
        
        This method takes an OpenAI Agents SDK Agent and converts it to a Contexa agent,
        extracting the tools, model configuration, and instructions to create an equivalent
        Contexa agent that maintains the same functionality.
        
        Args:
            openai_agent: The OpenAI Agents SDK Agent to convert
            name: Optional name override for the Contexa agent
            description: Optional description override for the Contexa agent
            
        Returns:
            A Contexa agent that wraps the OpenAI Agent functionality
            
        Raises:
            ImportError: If required dependencies are not installed
            TypeError: If the input is not a valid OpenAI Agent
            
        Example:
            ```python
            from openai_agents import Agent, function_tool
            from contexa_sdk.adapters import openai
            
            # Create an OpenAI agent
            @function_tool
            def get_weather(location: str) -> str:
                return f"Weather in {location} is sunny"
                
            oa_agent = Agent(
                name="Weather Assistant",
                instructions="You help users get weather information",
                tools=[get_weather],
                model="gpt-4o"
            )
            
            # Convert to Contexa agent
            contexa_agent = await openai.adapt_agent(oa_agent)
            result = await contexa_agent.run("What's the weather in Paris?")
            ```
        """
        try:
            from agents import Agent
        except ImportError:
            raise ImportError(
                "OpenAI Agents SDK not found. Install with `pip install openai-agents`."
            )
            
        if not isinstance(openai_agent, Agent):
            raise TypeError("openai_agent must be an OpenAI Agents SDK Agent object")
        
        # Extract agent metadata
        agent_name = name or getattr(openai_agent, 'name', 'Adapted OpenAI Agent')
        agent_description = description or getattr(openai_agent, 'description', '')
        instructions = getattr(openai_agent, 'instructions', 'You are a helpful assistant.')
        model_name = getattr(openai_agent, 'model', 'gpt-4o')
        
        # Convert OpenAI tools to Contexa tools
        contexa_tools = []
        openai_tools = getattr(openai_agent, 'tools', [])
        
        for i, oa_tool in enumerate(openai_tools):
            # Extract tool metadata
            tool_name = getattr(oa_tool, '__name__', f'tool_{i}')
            tool_description = getattr(oa_tool, '__doc__', f'Tool {tool_name}')
            
            # Create a wrapper function that calls the original OpenAI tool
            async def create_tool_wrapper(original_tool):
                async def tool_wrapper(**kwargs) -> str:
                    """Wrapper for OpenAI tool."""
                    try:
                        # Call the original OpenAI tool
                        if inspect.iscoroutinefunction(original_tool):
                            result = await original_tool(**kwargs)
                        else:
                            result = original_tool(**kwargs)
                        
                        # Ensure we return a string
                        return str(result)
                    except Exception as e:
                        return f"Error calling tool {tool_name}: {str(e)}"
                
                return tool_wrapper
            
            # Create the wrapper
            wrapper = await create_tool_wrapper(oa_tool)
            
            # Create a Contexa tool
            try:
                # Try to extract parameter schema from the OpenAI tool
                sig = inspect.signature(oa_tool)
                from pydantic import create_model
                
                fields = {}
                for param_name, param in sig.parameters.items():
                    if param.annotation != inspect.Parameter.empty:
                        fields[param_name] = (param.annotation, ...)
                    else:
                        fields[param_name] = (str, ...)  # Default to string
                
                schema = create_model(f"{tool_name.title()}Input", **fields)
                
            except Exception:
                # Fallback to a generic schema
                from pydantic import BaseModel
                class GenericInput(BaseModel):
                    input: str = "Generic input"
                schema = GenericInput
            
            contexa_tool = ContexaTool(
                func=wrapper,
                name=tool_name,
                description=tool_description,
                schema=schema
            )
            contexa_tools.append(contexa_tool)
        
        # Create a Contexa model
        from contexa_sdk.core.config import ContexaConfig
        config = ContexaConfig()
        
        contexa_model = ContexaModel(
            model_name=model_name,
            provider="openai",
            config=config
        )
        
        # Create the Contexa agent
        contexa_agent = ContexaAgent(
            tools=contexa_tools,
            model=contexa_model,
            name=agent_name,
            description=agent_description,
            system_prompt=instructions
        )
        
        # Store reference to the original OpenAI agent
        contexa_agent.metadata = contexa_agent.metadata or {}
        contexa_agent.metadata["original_openai_agent"] = openai_agent
        contexa_agent.metadata["adapted_from"] = "openai_agents_sdk"
        
        return contexa_agent


# Create a singleton instance
_adapter = OpenAIAdapter()

# Expose the adapter methods at the module level
tool = _adapter.tool
model = _adapter.model
agent = _adapter.agent
prompt = _adapter.prompt
adapt_assistant = _adapter.adapt_openai_assistant
adapt_agent = _adapter.adapt_openai_agent

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