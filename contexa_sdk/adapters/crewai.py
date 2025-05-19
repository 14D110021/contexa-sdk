"""CrewAI adapter for converting Contexa objects to CrewAI objects."""

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


class CrewAIAdapter(BaseAdapter):
    """CrewAI adapter for converting Contexa objects to CrewAI objects."""
    
    def tool(self, tool: ContexaTool) -> Any:
        """Convert a Contexa tool to a CrewAI tool.
        
        Args:
            tool: The Contexa tool to convert
            
        Returns:
            A CrewAI tool object
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
        
        Args:
            model: The Contexa model to convert
            
        Returns:
            A dictionary containing the model configuration with keys:
            - crewai_model: The model for CrewAI (string name or callable)
            - model_name: The model name
            - config: Additional configuration
            - provider: The model provider
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
        
        Args:
            agent: The Contexa agent to convert
            wrap_in_crew: Whether to wrap the agent in a Crew (default: True)
            
        Returns:
            A CrewAI Agent object or Crew object if wrap_in_crew is True
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
        
        Args:
            prompt: The Contexa prompt to convert
            
        Returns:
            A string template usable by CrewAI
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