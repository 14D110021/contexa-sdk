"""CrewAI adapter for converting Contexa objects to CrewAI objects.

This adapter provides integration between Contexa SDK and CrewAI, converting
Contexa tools, models, agents, and prompts to their CrewAI equivalents.

The CrewAI adapter enables seamless use of Contexa SDK components within
CrewAI workflows, agents, and crews. It handles the conversion of tool schemas,
model configurations, and agent definitions to ensure compatibility with CrewAI's
architecture and execution model.

Key features:
- Converting ContexaTool objects to CrewAI tool instances
- Adapting ContexaModel configurations to CrewAI-compatible models
- Creating CrewAI Agent instances from ContexaAgent objects
- Converting ContexaPrompt objects to CrewAI-compatible strings
- Supporting both individual agents and multi-agent crews
- Handling handoffs between Contexa agents and CrewAI agents

Usage:
    from contexa_sdk.adapters import crewai
    
    # Convert a Contexa tool to a CrewAI tool
    crew_tool = crewai.tool(my_contexa_tool)
    
    # Convert a Contexa agent to a CrewAI agent
    crew_agent = crewai.agent(my_contexa_agent, wrap_in_crew=False)
    
    # Convert a Contexa agent to a CrewAI crew (with a single agent)
    crew = crewai.agent(my_contexa_agent)
    
    # Run the CrewAI crew
    result = await crew.run("What's the weather in Paris?")

Requirements:
    This adapter requires CrewAI to be installed:
    `pip install contexa-sdk[crewai]`
"""

import inspect
import functools
import asyncio
import json
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, cast

from contexa_sdk.adapters.base import BaseAdapter
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel, ModelMessage
from contexa_sdk.core.agent import ContexaAgent, HandoffData
from contexa_sdk.core.prompt import ContexaPrompt

# Adapter version
__adapter_version__ = "0.1.0"


class CrewAIAdapter(BaseAdapter):
    """CrewAI adapter for converting Contexa objects to CrewAI objects.
    
    This adapter implements the BaseAdapter interface for the CrewAI framework.
    It provides methods to convert Contexa SDK core objects (tools, models, agents, 
    and prompts) to their CrewAI equivalents, enabling seamless integration
    between Contexa and CrewAI's multi-agent orchestration capabilities.
    
    The adapter handles conversion of tool schemas, model configurations, and agent
    definitions. It can create both individual CrewAI Agent instances and full Crew
    instances with default tasks. The adapter also supports handoffs between agents
    and provides utilities for multi-agent collaboration.
    
    Attributes:
        None
        
    Methods:
        tool: Convert a Contexa tool to a CrewAI tool
        model: Convert a Contexa model to a CrewAI agent model
        agent: Convert a Contexa agent to a CrewAI Agent or Crew
        prompt: Convert a Contexa prompt to a CrewAI-compatible string
        handoff_between_crew_agents: Handle handoff between CrewAI agents
    """
    
    def tool(self, tool: ContexaTool) -> Any:
        """Convert a Contexa tool to a CrewAI tool.
        
        This method takes a Contexa tool and converts it to a CrewAI tool
        that can be used with CrewAI agents and crews. It wraps the tool's
        functionality in a CrewAI tool decorator and handles the conversion
        between async and sync interfaces.
        
        Args:
            tool: The Contexa tool to convert. Can be either a ContexaTool instance
                 or a function decorated with ContexaTool.register.
            
        Returns:
            A CrewAI tool object that can be used with CrewAI agents.
            
        Raises:
            ImportError: If CrewAI dependencies are not installed.
            TypeError: If the input is not a valid ContexaTool instance.
            
        Example:
            ```python
            from contexa_sdk.core.tool import ContexaTool
            from contexa_sdk.adapters import crewai
            
            @ContexaTool.register(
                name="weather",
                description="Get weather information for a location"
            )
            async def get_weather(location: str) -> str:
                return f"Weather in {location} is sunny"
                
            # Convert to CrewAI tool
            crew_tool = crewai.tool(get_weather)
            ```
        """
        try:
            from crewai.tools import tool as crewai_tool_decorator
            import asyncio
        except ImportError:
            raise ImportError(
                "CrewAI not found. Install with `pip install contexa-sdk[crewai]`."
            )
            
        # Create a wrapper function for the tool
        @crewai_tool_decorator(tool.name)
        def contexa_tool_wrapper(**kwargs):
            """Tool docstring will be replaced."""
            # Run the async function in a new event loop
            return asyncio.run(tool(**kwargs))
            
        # Update the tool's docstring with the original description
        contexa_tool_wrapper.__doc__ = tool.description
        
        return contexa_tool_wrapper
        
    def model(self, model: ContexaModel) -> Any:
        """Convert a Contexa model to a CrewAI agent model.
        
        This method adapts a Contexa model to a CrewAI model representation by
        extracting the appropriate model identifier or creating a model callable
        for custom providers. It handles both standard LLM providers (OpenAI, Anthropic)
        and custom model interfaces.
        
        Args:
            model: The Contexa model to convert. This should be a ContexaModel instance
                  with provider, model_name, and other configuration attributes.
            
        Returns:
            A dictionary containing the model configuration with keys:
            - crewai_model: The model for CrewAI (string name or callable)
            - model_name: The model name
            - config: Additional configuration
            - provider: The model provider
            
        Raises:
            No specific exceptions are raised, as this method handles different
            model providers gracefully.
            
        Example:
            ```python
            from contexa_sdk.core.model import ContexaModel
            from contexa_sdk.adapters import crewai
            
            # For a standard provider
            model = ContexaModel(
                provider="openai",
                model_name="gpt-4o",
                temperature=0.7
            )
                
            # Convert to CrewAI model configuration
            crew_model_info = crewai.model(model)
            crew_model = crew_model_info["crewai_model"]
            
            # For a custom provider
            custom_model = ContexaModel(
                provider="custom",
                model_name="my-custom-model"
            )
            
            # This will create a callable adapter for the custom model
            custom_crew_model_info = crewai.model(custom_model)
            ```
        """
        # For CrewAI, we mostly just need to provide the model name
        # unless it's a local model or special case
        crewai_model = None
        
        if model.provider == "openai":
            crewai_model = model.model_name
        elif model.provider == "anthropic":
            crewai_model = model.model_name
        else:
            # Return a callable that interfaces with our model for custom providers
            async def model_callable(prompt: str) -> str:
                messages = [ModelMessage(role="user", content=prompt)]
                response = await model.generate(messages)
                return response.content
                
            # Wrap as a sync function for CrewAI
            def sync_model_callable(prompt: str) -> str:
                import asyncio
                return asyncio.run(model_callable(prompt))
                
            crewai_model = sync_model_callable
            
        # Return a standardized model info dictionary
        return {
            "crewai_model": crewai_model,
            "model_name": model.model_name,
            "config": model.config,
            "provider": model.provider,
        }
        
    def agent(self, agent: ContexaAgent, wrap_in_crew: bool = True) -> Any:
        """Convert a Contexa agent to a CrewAI agent.
        
        This method creates a CrewAI Agent from a Contexa agent, converting
        the agent's model, tools, and configuration. By default, it also wraps
        the agent in a CrewAI Crew with a default task, making it immediately
        usable as a complete workflow.
        
        Args:
            agent: The Contexa agent to convert. Should be a ContexaAgent instance with
                  model, tools, and other configuration attributes.
            wrap_in_crew: Whether to wrap the agent in a Crew (default: True). When True,
                         returns a complete CrewAI Crew. When False, returns just a CrewAI Agent.
            
        Returns:
            A CrewAI Agent object if wrap_in_crew is False, or a CrewAI Crew object if
            wrap_in_crew is True. Both objects have a __contexa_agent__ attribute for 
            reference and handoff support.
            
        Raises:
            ImportError: If CrewAI dependencies are not installed.
            
        Example:
            ```python
            from contexa_sdk.core.agent import ContexaAgent
            from contexa_sdk.core.model import ContexaModel
            from contexa_sdk.adapters import crewai
            
            agent = ContexaAgent(
                name="Assistant",
                model=ContexaModel(provider="openai", model_name="gpt-4o"),
                tools=[weather_tool, search_tool],
                system_prompt="You are a helpful assistant."
            )
                
            # Convert to CrewAI agent only
            crew_agent = crewai.agent(agent, wrap_in_crew=False)
            
            # Convert to CrewAI crew
            crew = crewai.agent(agent)
            result = crew.run("What's the weather in Paris?")
            ```
        """
        try:
            from crewai import Agent as CrewAgent, Task, Crew
        except ImportError:
            raise ImportError(
                "CrewAI not found. Install with `pip install contexa-sdk[crewai]`."
            )
            
        # Convert the model
        model_info = self.model(agent.model)
        crew_model = model_info["crewai_model"]
        
        # Convert the tools
        crew_tools = [self.tool(tool) for tool in agent.tools]
        
        # Create the CrewAI agent
        crew_agent = CrewAgent(
            role=agent.name,
            goal=agent.description or "Accomplish the task successfully",
            backstory=agent.system_prompt or "You are a helpful AI assistant",
            llm=crew_model,
            tools=crew_tools,
            verbose=True,
            allow_delegation=True  # Enable delegation by default
        )
        
        # Attach the original Contexa agent for reference
        crew_agent.__contexa_agent__ = agent
        
        # If requested to return just the agent, do so
        if not wrap_in_crew:
            return crew_agent
            
        # Otherwise, wrap in a simple Crew with a default task
        task = Task(
            description="Respond to user queries using your tools and knowledge",
            agent=crew_agent,
            expected_output="A detailed and helpful response"
        )
        
        crew = Crew(
            agents=[crew_agent],
            tasks=[task],
            verbose=True,
            process=Crew.SEQUENTIAL  # Default to sequential processing
        )
        
        # Add handoff method to the crew
        crew.__contexa_agent__ = agent
        
        return crew
        
    def prompt(self, prompt: ContexaPrompt) -> Any:
        """Convert a Contexa prompt to a format usable by CrewAI.
        
        This method converts a Contexa prompt template to a string format that
        can be used with CrewAI. For CrewAI, this is typically just the raw
        template string.
        
        Args:
            prompt: The Contexa prompt to convert. Should be a ContexaPrompt instance
                   with a template attribute.
            
        Returns:
            A string template usable by CrewAI.
            
        Example:
            ```python
            from contexa_sdk.core.prompt import ContexaPrompt
            from contexa_sdk.adapters import crewai
            
            prompt = ContexaPrompt(
                template="You are an assistant that helps with {task}."
            )
                
            # Convert to CrewAI-compatible string
            crew_prompt = crewai.prompt(prompt)
            ```
        """
        # CrewAI typically just uses string templates
        return prompt.template
    
    async def handoff_between_crew_agents(
        self,
        source_agent: ContexaAgent,
        target: Any,  # CrewAI Crew object or Agent object
        query: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Handle handoff specifically between CrewAI agents.
        
        This method is used to hand off from a Contexa agent to a CrewAI agent,
        using CrewAI's native delegation mechanism.
        
        Args:
            source_agent: The Contexa agent handing off the task
            target: The CrewAI crew or agent receiving the task
            query: The query to send to the target
            context: Additional context to pass to the target
            metadata: Additional metadata for the handoff
            
        Returns:
            The target's response
        """
        try:
            from crewai import Crew, Agent as CrewAgent, Task
        except ImportError:
            raise ImportError(
                "CrewAI not found. Install with `pip install contexa-sdk[crewai]`."
            )
            
        # Check if the target is a Crew or Agent and handle accordingly
        if not (isinstance(target, Crew) or isinstance(target, CrewAgent)):
            raise TypeError("target must be a CrewAI Crew or Agent object")
            
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
        
        # If the target is a single agent, wrap it in a Crew for consistent handling
        if isinstance(target, CrewAgent):
            # Create a task with the context for the agent
            task = Task(
                description=query,
                expected_output="Detailed response to the query",
                agent=target,
                context=json.dumps(handoff_data.context),
            )
            
            # Update the agent with handoff context
            updated_backstory = (
                f"{target.backstory}\n\n"
                f"IMPORTANT CONTEXT: This is a handoff from agent '{source_agent.name}'. "
                f"Previous context: {json.dumps(handoff_data.context)}"
            )
            target.backstory = updated_backstory
            
            # Create a crew with the agent
            target_crew = Crew(
                agents=[target],
                tasks=[task],
                verbose=True,
                process=Crew.SEQUENTIAL
            )
        else:
            # Use the existing crew
            target_crew = target
            
            # If there's only one agent in the crew, target it directly 
            if len(target_crew.agents) == 1:
                crew_agent = target_crew.agents[0]
                
                # Update the CrewAI agent with handoff context
                # Provide context as both backstory and memory for comprehensive awareness
                updated_backstory = (
                    f"{crew_agent.backstory}\n\n"
                    f"IMPORTANT CONTEXT: This is a handoff from agent '{source_agent.name}'. "
                    f"Previous context: {json.dumps(handoff_data.context)}"
                )
                
                crew_agent.backstory = updated_backstory
                
                # Create a new task with the handed-off query
                task = Task(
                    description=query,
                    expected_output="Detailed response to the query",
                    agent=crew_agent,
                    context=json.dumps(handoff_data.context),
                )
                
                # Update the crew's tasks
                target_crew.tasks = [task]
            else:
                # For multiple agents, create a task for the first agent
                # and set up delegation between agents
                tasks = []
                
                # Create a context string to share with all agents
                shared_context = (
                    f"IMPORTANT CONTEXT: This is a handoff from agent '{source_agent.name}'. "
                    f"Task: {query}\n"
                    f"Context: {json.dumps(handoff_data.context)}"
                )
                
                # Update each agent's backstory with the context
                for crew_agent in target_crew.agents:
                    updated_backstory = (
                        f"{crew_agent.backstory}\n\n{shared_context}"
                    )
                    crew_agent.backstory = updated_backstory
                
                # Create tasks for all agents, with the first agent as the entry point
                primary_agent = target_crew.agents[0]
                primary_task = Task(
                    description=f"Primary task from handoff: {query}",
                    expected_output="Comprehensive response integrating all agent inputs",
                    agent=primary_agent,
                    context=json.dumps(handoff_data.context),
                )
                tasks.append(primary_task)
                
                # Create supporting tasks for other agents
                for i, crew_agent in enumerate(target_crew.agents[1:], 1):
                    supporting_task = Task(
                        description=f"Support primary agent with specialized expertise on: {query}",
                        expected_output="Specialized analysis or response",
                        agent=crew_agent,
                        context=json.dumps(handoff_data.context),
                    )
                    tasks.append(supporting_task)
                
                # Configure task dependencies to enable delegation
                for i in range(1, len(tasks)):
                    tasks[i].context = f"{tasks[i].context}\nThis task supports the primary task."
                
                # Update the crew with the new tasks
                target_crew.tasks = tasks
                
                # Set process to hierarchical if there are multiple agents
                if len(target_crew.agents) > 1:
                    target_crew.process = Crew.HIERARCHICAL
            
        # Execute the crew to run the task
        response = target_crew.kickoff(inputs={"handoff_context": json.dumps(handoff_data.context)})
        
        # Update the handoff data with the result
        handoff_data.result = response
        
        # Update the Contexa agent associated with the target if it exists
        if isinstance(target, Crew) and hasattr(target, "__contexa_agent__"):
            target_agent = target.__contexa_agent__
            target_agent.receive_handoff(handoff_data)
        elif isinstance(target, CrewAgent) and hasattr(target, "__contexa_agent__"):
            target_agent = target.__contexa_agent__
            target_agent.receive_handoff(handoff_data)
        
        return response


# Create a singleton instance
_adapter = CrewAIAdapter()

# Expose the adapter methods at the module level
tool = _adapter.tool
model = _adapter.model
def agent(agent_obj: ContexaAgent, wrap_in_crew: bool = True) -> Any:
    """Convert a Contexa agent to a CrewAI agent or crew.
    
    Args:
        agent_obj: The Contexa agent to convert
        wrap_in_crew: Whether to wrap the agent in a Crew (default: True)
        
    Returns:
        A CrewAI Agent object or Crew object based on wrap_in_crew parameter
    """
    return _adapter.agent(agent_obj, wrap_in_crew=wrap_in_crew)
prompt = _adapter.prompt

# Expose handoff method at the module level
async def handoff(
    source_agent: ContexaAgent,
    target: Any,
    query: str,
    context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Handle handoff from a Contexa agent to a CrewAI agent/crew."""
    return await _adapter.handoff_between_crew_agents(
        source_agent=source_agent,
        target=target,
        query=query,
        context=context,
        metadata=metadata,
    ) 