"""LangChain adapter for converting Contexa objects to LangChain objects."""

import inspect
import json
import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from contexa_sdk.adapters.base import BaseAdapter
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel, ModelMessage
from contexa_sdk.core.agent import ContexaAgent, HandoffData
from contexa_sdk.core.prompt import ContexaPrompt


class LangChainAdapter(BaseAdapter):
    """LangChain adapter for converting Contexa objects to LangChain objects."""
    
    def tool(self, tool: ContexaTool) -> Any:
        """Convert a Contexa tool to a LangChain tool.
        
        Args:
            tool: The Contexa tool to convert
            
        Returns:
            A LangChain BaseTool object
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
        
        Args:
            model: The Contexa model to convert
            
        Returns:
            A dictionary containing the model configuration with keys:
            - langchain_model: The LangChain model object
            - model_name: The model name
            - config: Additional configuration
            - provider: The model provider
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
        
        Args:
            agent: The Contexa agent to convert
            
        Returns:
            A LangChain AgentExecutor
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


# Create a singleton instance
_adapter = LangChainAdapter()

# Expose the adapter methods at the module level
tool = _adapter.tool
model = _adapter.model
agent = _adapter.agent
prompt = _adapter.prompt

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