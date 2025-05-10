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
            A compatible string model name or custom callable model for CrewAI
        """
        # For CrewAI, we mostly just need to provide the model name
        # unless it's a local model or special case
        if model.provider == "openai":
            return model.model_name
        elif model.provider == "anthropic":
            return model.model_name
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
                
            return sync_model_callable
            
    def agent(self, agent: ContexaAgent) -> Any:
        """Convert a Contexa agent to a CrewAI agent.
        
        Args:
            agent: The Contexa agent to convert
            
        Returns:
            A CrewAI Agent object
        """
        try:
            from crewai import Agent as CrewAgent, Task, Crew
        except ImportError:
            raise ImportError(
                "CrewAI not found. Install with `pip install contexa-sdk[crewai]`."
            )
            
        # Convert the model
        crew_model = self.model(agent.model)
        
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
        
        # Wrap in a simple Crew with a default task
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
        target_crew: Any,  # CrewAI Crew object
        query: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Handle handoff specifically between CrewAI agents.
        
        This method is used to hand off from a Contexa agent to a CrewAI agent,
        using CrewAI's native delegation mechanism.
        
        Args:
            source_agent: The Contexa agent handing off the task
            target_crew: The CrewAI crew receiving the task
            query: The query to send to the target crew
            context: Additional context to pass to the target crew
            metadata: Additional metadata for the handoff
            
        Returns:
            The target crew's response
        """
        try:
            from crewai import Crew, Agent as CrewAgent
        except ImportError:
            raise ImportError(
                "CrewAI not found. Install with `pip install contexa-sdk[crewai]`."
            )
            
        if not isinstance(target_crew, Crew):
            raise TypeError("target_crew must be a CrewAI Crew object")
            
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
        
        # Create a task with the context for the crew
        try:
            from crewai import Task
        except ImportError:
            raise ImportError(
                "CrewAI not found. Install with `pip install contexa-sdk[crewai]`."
            )
            
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
            
        # Execute the crew to run the task
        response = target_crew.kickoff(inputs={"handoff_context": json.dumps(handoff_data.context)})
        
        # Update the handoff data with the result
        handoff_data.result = response
        
        # Also update the Contexa agent associated with the crew if it exists
        if hasattr(target_crew, "__contexa_agent__"):
            # Add the handoff to the target Contexa agent's memory
            target_agent = target_crew.__contexa_agent__
            target_agent.receive_handoff(handoff_data)
        
        return response


# Create a singleton instance
_adapter = CrewAIAdapter()

# Expose the adapter methods at the module level
tool = _adapter.tool
model = _adapter.model
agent = _adapter.agent
prompt = _adapter.prompt

# Expose handoff method at the module level
async def handoff(
    source_agent: ContexaAgent,
    target_crew: Any,
    query: str,
    context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Handle handoff from a Contexa agent to a CrewAI agent/crew."""
    return await _adapter.handoff_between_crew_agents(
        source_agent=source_agent,
        target_crew=target_crew,
        query=query,
        context=context,
        metadata=metadata,
    ) 