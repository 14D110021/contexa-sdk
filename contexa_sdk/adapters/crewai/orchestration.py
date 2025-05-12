"""CrewAI orchestration support for Contexa SDK.

This module provides conversion functions between Contexa orchestration objects
and CrewAI's built-in crew objects, enabling sophisticated agent workflows.
"""

import asyncio
from typing import Any, Dict, List, Optional, Union, Callable

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.orchestration import AgentTeam, TaskHandoff
from contexa_sdk.adapters.crewai import tool, model, agent


class CrewOrchestrationConverter:
    """Converter between Contexa orchestration and CrewAI structures."""
    
    def __init__(self):
        """Initialize the CrewAI orchestration converter."""
        self._check_crewai_available()
    
    def _check_crewai_available(self):
        """Check if CrewAI is available."""
        try:
            from crewai import Crew, Agent, Task
        except ImportError:
            raise ImportError(
                "CrewAI not found. Install with `pip install crewai`."
            )
    
    def agent_team_to_crew(self, team: AgentTeam) -> Any:
        """Convert a Contexa AgentTeam to a CrewAI Crew.
        
        Args:
            team: The Contexa AgentTeam to convert
            
        Returns:
            A CrewAI Crew object
        """
        from crewai import Crew, Agent, Task
        
        # Convert all agents to CrewAI agents
        crew_agents = []
        for agent_id, agent_info in team.agents.items():
            contexa_agent = agent_info["agent"]
            agent_role = agent_info.get("role", "assistant")
            
            # Convert the agent to CrewAI format
            crew_agent = agent(contexa_agent)
            
            # Extract the CrewAI agent from the crew
            if hasattr(crew_agent, "agents") and len(crew_agent.agents) > 0:
                crew_agent = crew_agent.agents[0]
                
            # Store the original agent_id for reference
            setattr(crew_agent, "__contexa_agent_id__", agent_id)
                
            crew_agents.append(crew_agent)
        
        # Create tasks based on the team's description
        tasks = []
        for handoff in team.handoffs:
            # Find the CrewAI agents representing the sender and recipient
            sender_agent = None
            recipient_agent = None
            
            for crew_agent in crew_agents:
                agent_id = getattr(crew_agent, "__contexa_agent_id__", None)
                if agent_id == handoff.sender.agent_id:
                    sender_agent = crew_agent
                elif agent_id == handoff.recipient.agent_id:
                    recipient_agent = crew_agent
            
            if sender_agent and recipient_agent:
                # Create a task for this handoff
                task = Task(
                    description=handoff.task_description,
                    agent=recipient_agent,
                    expected_output=f"Results from {handoff.task_description}",
                    context={
                        "handoff_source": sender_agent.role,
                        "handoff_type": "contexa_handoff"
                    }
                )
                tasks.append(task)
        
        # If no tasks were created from handoffs, create a default task for each agent
        if not tasks:
            for crew_agent in crew_agents:
                task = Task(
                    description=f"Perform tasks related to your role as {crew_agent.role}",
                    agent=crew_agent,
                    expected_output="Completed results"
                )
                tasks.append(task)
        
        # Create the CrewAI Crew
        crew = Crew(
            agents=crew_agents,
            tasks=tasks,
            verbose=True,
            process=Crew.SEQUENTIAL  # Use sequential processing by default
        )
        
        # Store reference to original Contexa team
        crew.__contexa_team__ = team
        
        return crew
    
    def task_handoff_to_crewai_task(self, handoff: TaskHandoff) -> Any:
        """Convert a Contexa TaskHandoff to a CrewAI Task.
        
        Args:
            handoff: The Contexa TaskHandoff to convert
            
        Returns:
            A CrewAI Task object
        """
        from crewai import Task
        
        # Convert the recipient agent to CrewAI
        crew_agent = agent(handoff.recipient)
        
        # Extract the CrewAI agent from the crew wrapper
        if hasattr(crew_agent, "agents") and len(crew_agent.agents) > 0:
            crew_agent = crew_agent.agents[0]
        
        # Create a task for this handoff
        task = Task(
            description=handoff.task_description,
            agent=crew_agent,
            expected_output=f"Results from {handoff.task_description}",
            context={
                "handoff_source": handoff.sender.name,
                "handoff_id": handoff.handoff_id,
                "handoff_type": "contexa_handoff"
            }
        )
        
        return task
    
    async def adapt_crew_to_agent_team(self, crew: Any) -> AgentTeam:
        """Convert a CrewAI Crew to a Contexa AgentTeam.
        
        Args:
            crew: The CrewAI Crew to adapt
            
        Returns:
            A Contexa AgentTeam
        """
        from crewai import Crew
        
        # If this crew was made from a Contexa team, return the original
        if hasattr(crew, "__contexa_team__"):
            return crew.__contexa_team__
        
        # Create a new AgentTeam
        team = AgentTeam(
            name=getattr(crew, "name", "CrewAI Team"),
            description=getattr(crew, "description", "A team adapted from CrewAI")
        )
        
        # Convert all CrewAI agents to Contexa agents
        for crew_agent in crew.agents:
            # Check if this agent has a reference to a Contexa agent
            if hasattr(crew_agent, "__contexa_agent__"):
                contexa_agent = crew_agent.__contexa_agent__
            else:
                # Create a new Contexa agent based on CrewAI agent properties
                from contexa_sdk.core.model import ContexaModel
                
                model_name = getattr(crew_agent, "model_name", "gpt-4")
                
                contexa_model = ContexaModel(
                    provider="openai", 
                    model_name=model_name
                )
                
                # Convert CrewAI tools to Contexa tools (simplified)
                tools = []
                
                contexa_agent = ContexaAgent(
                    name=crew_agent.role,
                    description=crew_agent.goal,
                    system_prompt=crew_agent.backstory,
                    model=contexa_model,
                    tools=tools
                )
            
            # Add to the team
            team.add_agent(contexa_agent, role="specialist")
            
        # Create handoffs based on tasks if available
        for task in crew.tasks:
            # Find the recipient agent
            recipient_agent = None
            for contexa_agent in team.agents.values():
                if contexa_agent["agent"].name == task.agent.role:
                    recipient_agent = contexa_agent["agent"]
                    break
            
            if recipient_agent and len(team.agents) > 1:
                # Just pick the first other agent as sender for now
                sender_agent = None
                for agent_info in team.agents.values():
                    if agent_info["agent"] != recipient_agent:
                        sender_agent = agent_info["agent"]
                        break
                
                if sender_agent:
                    handoff = TaskHandoff(
                        sender=sender_agent,
                        recipient=recipient_agent,
                        task_description=task.description
                    )
                    team.add_handoff(handoff)
        
        return team


# Create a singleton converter
converter = CrewOrchestrationConverter()

# Export functions
def agent_team_to_crew(team: AgentTeam) -> Any:
    """Convert a Contexa AgentTeam to a CrewAI Crew."""
    return converter.agent_team_to_crew(team)

def task_handoff_to_crewai_task(handoff: TaskHandoff) -> Any:
    """Convert a Contexa TaskHandoff to a CrewAI Task."""
    return converter.task_handoff_to_crewai_task(handoff)

async def adapt_crew_to_agent_team(crew: Any) -> AgentTeam:
    """Convert a CrewAI Crew to a Contexa AgentTeam."""
    return await converter.adapt_crew_to_agent_team(crew) 