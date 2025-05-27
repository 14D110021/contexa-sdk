"""LangChain adapter for converting Contexa objects to LangChain objects.

This adapter provides integration between Contexa SDK and LangChain, converting
Contexa tools, models, agents, and prompts to their LangChain equivalents.

The LangChain adapter enables seamless use of Contexa SDK components within
LangChain workflows, agents, and applications. It handles the conversion of schema
types, function signatures, and object attributes to ensure compatibility.

Key features:
- Converting ContexaTool objects to LangChain BaseTool instances
- Adapting ContexaModel configurations to LangChain chat models
- Creating LangChain AgentExecutor instances from ContexaAgent objects
- Converting ContexaPrompt objects to LangChain prompt templates
- Handling handoffs between Contexa agents and LangChain agents

Usage:
    from contexa_sdk.adapters import langchain
    
    # Convert a Contexa tool to a LangChain tool
    lc_tool = langchain.tool(my_contexa_tool)
    
    # Convert a Contexa model to a LangChain model
    lc_model = langchain.model(my_contexa_model)
    
    # Convert a Contexa agent to a LangChain agent
    lc_agent = langchain.agent(my_contexa_agent)
    
    # Run the LangChain agent
    result = await lc_agent.invoke("What's the weather in Paris?")

Requirements:
    This adapter requires LangChain to be installed:
    `pip install contexa-sdk[langchain]`
"""

import inspect
import json
import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from contexa_sdk.adapters.base import BaseAdapter
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel, ModelMessage
from contexa_sdk.core.agent import ContexaAgent, HandoffData
from contexa_sdk.core.prompt import ContexaPrompt

# Adapter version
__adapter_version__ = "0.1.0"


class LangChainAdapter(BaseAdapter):
    """LangChain adapter for converting Contexa objects to LangChain objects.
    
    This adapter implements the BaseAdapter interface for the LangChain framework.
    It provides methods to convert Contexa SDK core objects (tools, models, agents, 
    and prompts) to their LangChain equivalents, enabling seamless integration
    between Contexa and LangChain.
    
    The adapter handles conversion of schema types, function signatures, memory
    management, and other framework-specific details to ensure compatibility and
    proper functionality.
    
    Attributes:
        None
        
    Methods:
        tool: Convert a Contexa tool to a LangChain BaseTool
        model: Convert a Contexa model to a LangChain chat model
        agent: Convert a Contexa agent to a LangChain AgentExecutor
        prompt: Convert a Contexa prompt to a LangChain prompt template
        handoff_to_langchain_agent: Handle handoff to a LangChain agent
    """
    
    def tool(self, tool: ContexaTool) -> Any:
        """Convert a Contexa tool to a LangChain tool.
        
        This method takes a Contexa tool and converts it to a LangChain BaseTool
        subclass that can be used with LangChain agents and chains. It handles
        converting the tool's input schema to a Pydantic model and wraps the tool's
        functionality in appropriate LangChain-compatible methods.
        
        Args:
            tool: The Contexa tool to convert. Can be either a ContexaTool instance
                 or a function decorated with ContexaTool.register.
            
        Returns:
            A LangChain BaseTool object that can be used with LangChain agents.
            
        Raises:
            ImportError: If LangChain dependencies are not installed.
            TypeError: If the input is not a valid ContexaTool instance.
            
        Example:
            ```python
            from contexa_sdk.core.tool import ContexaTool
            from contexa_sdk.adapters import langchain
            
            @ContexaTool.register(
                name="weather",
                description="Get weather information for a location"
            )
            async def get_weather(location: str) -> str:
                return f"Weather in {location} is sunny"
                
            # Convert to LangChain tool
            lc_tool = langchain.tool(get_weather)
            ```
        """
        try:
            from langchain_core.tools import BaseTool, StructuredTool
            from langchain_core.pydantic_v1 import BaseModel, create_model
            import asyncio
        except ImportError:
            raise ImportError(
                "LangChain not found. Install with `pip install contexa-sdk[langchain]`."
            )
            
        # Create a Pydantic model for the tool's input
        fields = {}
        schema_props = tool.schema.model_json_schema().get("properties", {})
        for name, prop in schema_props.items():
            fields[name] = (Any, ...)
            
        ArgsSchema = create_model(f"{tool.name.title()}Schema", **fields)
        
        # Create the LangChain tool
        class LangChainTool(BaseTool):
            name = tool.name
            description = tool.description
            args_schema = ArgsSchema
            
            def _run(self, **kwargs):
                # For sync execution, run the async method in a new event loop
                return asyncio.run(self._arun(**kwargs))
                
            async def _arun(self, **kwargs):
                return await tool(**kwargs)
                
        return LangChainTool()
        
    def model(self, model: ContexaModel) -> Any:
        """Convert a Contexa model to a LangChain chat model.
        
        This method adapts a Contexa model to a LangChain chat model by creating
        a custom LangChain BaseChatModel implementation that uses the Contexa
        model for generating responses. It handles message format conversion and
        provides a standard LangChain interface.
        
        Args:
            model: The Contexa model to convert. This should be a ContexaModel instance
                  with provider, model_name, and other configuration attributes.
            
        Returns:
            A dictionary containing the model configuration with keys:
            - langchain_model: The LangChain model object (BaseChatModel instance)
            - model_name: The model name
            - config: Additional configuration
            - provider: The model provider
            
        Raises:
            ImportError: If LangChain dependencies are not installed.
            
        Example:
            ```python
            from contexa_sdk.core.model import ContexaModel
            from contexa_sdk.adapters import langchain
            
            model = ContexaModel(
                provider="openai",
                model_name="gpt-4o",
                temperature=0.7
            )
                
            # Convert to LangChain model
            lc_model_info = langchain.model(model)
            lc_model = lc_model_info["langchain_model"]
            ```
        """
        try:
            from langchain_core.language_models.chat_models import BaseChatModel
            from langchain_core.messages import (
                AIMessage,
                BaseMessage,
                HumanMessage,
                SystemMessage,
            )
            from langchain_core.outputs import ChatGeneration, ChatResult
        except ImportError:
            raise ImportError(
                "LangChain not found. Install with `pip install contexa-sdk[langchain]`."
            )
            
        # Create a custom chat model that uses our ContexaModel
        class ContexaChatModel(BaseChatModel):
            model_name = model.model_name
            streaming = False
            
            def _generate(
                self, messages: List[BaseMessage], stop: Optional[List[str]] = None
            ) -> ChatResult:
                import asyncio
                return asyncio.run(self._agenerate(messages, stop))
                
            async def _agenerate(
                self, messages: List[BaseMessage], stop: Optional[List[str]] = None
            ) -> ChatResult:
                # Convert LangChain messages to our format
                contexa_messages = []
                for message in messages:
                    if isinstance(message, SystemMessage):
                        contexa_messages.append(
                            ModelMessage(role="system", content=message.content)
                        )
                    elif isinstance(message, HumanMessage):
                        contexa_messages.append(
                            ModelMessage(role="user", content=message.content)
                        )
                    elif isinstance(message, AIMessage):
                        contexa_messages.append(
                            ModelMessage(role="assistant", content=message.content)
                        )
                    else:
                        # Try to handle other message types gracefully
                        contexa_messages.append(
                            ModelMessage(
                                role=getattr(message, "type", "user"),
                                content=message.content
                            )
                        )
                        
                # Generate the response using our model
                response = await model.generate(contexa_messages, stop=stop)
                
                # Convert back to LangChain format
                message = AIMessage(content=response.content)
                generation = ChatGeneration(message=message)
                
                return ChatResult(generations=[generation])
                
            @property
            def _llm_type(self) -> str:
                return f"contexa-{model.provider}"
        
        langchain_model = ContexaChatModel()
        
        # Return a standardized model info dictionary
        return {
            "langchain_model": langchain_model,
            "model_name": model.model_name,
            "config": model.config,
            "provider": model.provider,
        }
        
    def agent(self, agent: ContexaAgent) -> Any:
        """Convert a Contexa agent to a LangChain agent.
        
        This method creates a LangChain AgentExecutor from a Contexa agent, converting
        the agent's model, tools, and prompts to their LangChain equivalents. The resulting
        AgentExecutor can be used within LangChain workflows and applications.
        
        Args:
            agent: The Contexa agent to convert. Should be a ContexaAgent instance with
                  model, tools, and other configuration attributes.
            
        Returns:
            A LangChain AgentExecutor that can be used to run queries and tasks.
            The executor has a __contexa_agent__ attribute for reference and handoff support.
            
        Raises:
            ImportError: If LangChain dependencies are not installed.
            
        Example:
            ```python
            from contexa_sdk.core.agent import ContexaAgent
            from contexa_sdk.core.model import ContexaModel
            from contexa_sdk.adapters import langchain
            
            agent = ContexaAgent(
                name="Assistant",
                model=ContexaModel(provider="openai", model_name="gpt-4o"),
                tools=[weather_tool, search_tool],
                system_prompt="You are a helpful assistant."
            )
                
            # Convert to LangChain agent
            lc_agent = langchain.agent(agent)
            result = await lc_agent.invoke("What's the weather in Paris?")
            ```
        """
        try:
            from langchain.agents import AgentExecutor
            from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
            from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        except ImportError:
            raise ImportError(
                "LangChain not found. Install with `pip install contexa-sdk[langchain]`."
            )
            
        # Convert the model
        model_info = self.model(agent.model)
        lc_model = model_info["langchain_model"]
        
        # Convert the tools
        lc_tools = [self.tool(tool) for tool in agent.tools]
        
        # Create a system message with the agent's system prompt
        system_message = agent.system_prompt or "You are a helpful assistant."
        
        # Create a prompt for the agent
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Initialize the agent
        lc_agent = OpenAIFunctionsAgent(
            llm=lc_model,
            tools=lc_tools,
            prompt=prompt
        )
        
        # Create the agent executor
        lc_agent_executor = AgentExecutor(
            agent=lc_agent,
            tools=lc_tools,
            verbose=True,
        )
        
        # Store the original Contexa agent for reference and handoff support
        lc_agent_executor.__contexa_agent__ = agent
        
        return lc_agent_executor
        
    def prompt(self, prompt: ContexaPrompt) -> Any:
        """Convert a Contexa prompt to a LangChain prompt.
        
        Args:
            prompt: The Contexa prompt to convert
            
        Returns:
            A LangChain ChatPromptTemplate
        """
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.messages import SystemMessage, HumanMessagePromptTemplate
        except ImportError:
            raise ImportError(
                "LangChain not found. Install with `pip install contexa-sdk[langchain]`."
            )
            
        # Very simple implementation - could be improved based on prompt name/type
        return ChatPromptTemplate.from_messages([
            SystemMessage(content="You are a helpful assistant."),
            HumanMessagePromptTemplate.from_template(prompt.template),
        ])
    
    async def handoff_to_langchain_agent(
        self,
        source_agent: ContexaAgent,
        target_agent_executor: Any,  # LangChain AgentExecutor
        query: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Handle handoff to a LangChain agent.
        
        Args:
            source_agent: The Contexa agent handing off the task
            target_agent_executor: The LangChain AgentExecutor to hand off to
            query: The query to send to the target agent
            context: Additional context to pass to the target agent
            metadata: Additional metadata for the handoff
            
        Returns:
            The target agent's response
        """
        try:
            from langchain.agents import AgentExecutor
            from langchain_core.messages import HumanMessage, SystemMessage
        except ImportError:
            raise ImportError(
                "LangChain not found. Install with `pip install contexa-sdk[langchain]`."
            )
            
        if not isinstance(target_agent_executor, AgentExecutor):
            raise TypeError("target_agent_executor must be a LangChain AgentExecutor")
            
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
        
        # Format the query to include handoff context
        context_str = json.dumps(handoff_data.context, indent=2)
        enhanced_query = (
            f"[Task handoff from agent '{source_agent.name}']\n\n"
            f"CONTEXT: {context_str}\n\n"
            f"TASK: {query}"
        )
        
        # Run the target agent with the enhanced query
        response = await asyncio.to_thread(target_agent_executor.invoke, {"input": enhanced_query})
        
        # Extract result
        result = response.get("output", str(response))
        
        # Update the handoff data with the result
        handoff_data.result = result
        
        # Also update the Contexa agent associated with the LangChain agent if it exists
        if hasattr(target_agent_executor, "__contexa_agent__"):
            target_agent = target_agent_executor.__contexa_agent__
            target_agent.receive_handoff(handoff_data)
            
        return result

    async def adapt_langchain_agent(
        self, 
        langchain_agent_executor: Any,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> ContexaAgent:
        """Adapt a LangChain AgentExecutor to a Contexa agent.
        
        This method takes a LangChain AgentExecutor and converts it to a Contexa agent,
        extracting the tools, model configuration, and instructions to create an equivalent
        Contexa agent that maintains the same functionality.
        
        Args:
            langchain_agent_executor: The LangChain AgentExecutor to convert
            name: Optional name override for the Contexa agent
            description: Optional description override for the Contexa agent
            
        Returns:
            A Contexa agent that wraps the LangChain AgentExecutor functionality
            
        Raises:
            ImportError: If required dependencies are not installed
            TypeError: If the input is not a valid LangChain AgentExecutor
            
        Example:
            ```python
            from langchain.agents import AgentExecutor
            from contexa_sdk.adapters import langchain
            
            # Create a LangChain agent
            lc_agent = AgentExecutor(...)
            
            # Convert to Contexa agent
            contexa_agent = await langchain.adapt_agent(lc_agent)
            result = await contexa_agent.run("What's the weather in Paris?")
            ```
        """
        try:
            from langchain.agents import AgentExecutor
        except ImportError:
            raise ImportError(
                "LangChain not found. Install with `pip install contexa-sdk[langchain]`."
            )
            
        if not isinstance(langchain_agent_executor, AgentExecutor):
            raise TypeError("langchain_agent_executor must be a LangChain AgentExecutor object")
        
        # Extract agent metadata
        agent_name = name or getattr(langchain_agent_executor, 'name', 'Adapted LangChain Agent')
        agent_description = description or getattr(langchain_agent_executor, 'description', '')
        
        # Extract tools from the LangChain agent
        contexa_tools = []
        lc_tools = getattr(langchain_agent_executor, 'tools', [])
        
        for i, lc_tool in enumerate(lc_tools):
            # Extract tool metadata
            tool_name = getattr(lc_tool, 'name', f'tool_{i}')
            tool_description = getattr(lc_tool, 'description', f'Tool {tool_name}')
            
            # Create a wrapper function that calls the original LangChain tool
            async def create_tool_wrapper(original_tool):
                async def tool_wrapper(**kwargs) -> str:
                    """Wrapper for LangChain tool."""
                    try:
                        # Call the original LangChain tool
                        if hasattr(original_tool, '_arun'):
                            result = await original_tool._arun(**kwargs)
                        elif hasattr(original_tool, '_run'):
                            result = original_tool._run(**kwargs)
                        else:
                            # Fallback to invoke if available
                            result = await original_tool.ainvoke(kwargs) if hasattr(original_tool, 'ainvoke') else original_tool.invoke(kwargs)
                        
                        # Ensure we return a string
                        return str(result)
                    except Exception as e:
                        return f"Error calling tool {tool_name}: {str(e)}"
                
                return tool_wrapper
            
            # Create the wrapper
            wrapper = await create_tool_wrapper(lc_tool)
            
            # Create a Contexa tool
            try:
                # Try to extract parameter schema from the LangChain tool
                args_schema = getattr(lc_tool, 'args_schema', None)
                if args_schema:
                    schema = args_schema
                else:
                    # Fallback to a generic schema
                    from pydantic import BaseModel
                    class GenericInput(BaseModel):
                        input: str = "Generic input"
                    schema = GenericInput
                
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
        
        # Try to extract model information from the LangChain agent
        model_name = "gpt-4o"  # Default
        if hasattr(langchain_agent_executor, 'agent') and hasattr(langchain_agent_executor.agent, 'llm'):
            llm = langchain_agent_executor.agent.llm
            if hasattr(llm, 'model_name'):
                model_name = llm.model_name
            elif hasattr(llm, 'model'):
                model_name = llm.model
        
        contexa_model = ContexaModel(
            model_name=model_name,
            provider="openai",  # Default to OpenAI
            config=config
        )
        
        # Extract system prompt if available
        system_prompt = "You are a helpful assistant."
        if hasattr(langchain_agent_executor, 'agent') and hasattr(langchain_agent_executor.agent, 'prompt'):
            prompt = langchain_agent_executor.agent.prompt
            if hasattr(prompt, 'messages') and prompt.messages:
                for message in prompt.messages:
                    if hasattr(message, 'content') and 'system' in str(type(message)).lower():
                        system_prompt = message.content
                        break
        
        # Create the Contexa agent
        contexa_agent = ContexaAgent(
            tools=contexa_tools,
            model=contexa_model,
            name=agent_name,
            description=agent_description,
            system_prompt=system_prompt
        )
        
        # Store reference to the original LangChain agent
        contexa_agent.metadata = contexa_agent.metadata or {}
        contexa_agent.metadata["original_langchain_agent"] = langchain_agent_executor
        contexa_agent.metadata["adapted_from"] = "langchain_agent_executor"
        
        return contexa_agent


# Create a singleton instance
_adapter = LangChainAdapter()

# Expose the adapter methods at the module level
tool = _adapter.tool
model = _adapter.model
agent = _adapter.agent
prompt = _adapter.prompt
adapt_agent = _adapter.adapt_langchain_agent

# Expose handoff method at the module level
async def handoff(
    source_agent: ContexaAgent,
    target_agent_executor: Any,
    query: str,
    context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Handle handoff from a Contexa agent to a LangChain agent."""
    return await _adapter.handoff_to_langchain_agent(
        source_agent=source_agent,
        target_agent_executor=target_agent_executor,
        query=query,
        context=context,
        metadata=metadata,
    ) 