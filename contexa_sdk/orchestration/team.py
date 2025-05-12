"""
Team organization components for agent collaboration.

This module defines structures for organizing agents into functional teams
with roles, communication, and resource sharing.
"""

from typing import Dict, Any, List, Optional
import uuid

class AgentTeam:
    """Group of agents organized around a functional area.
    
    An AgentTeam provides a logical grouping of agents with complementary skills and roles,
    similar to departmental teams in human organizations. Teams can have designated
    leaders, shared resources, and defined communication patterns.
    
    Attributes:
        name (str): Name of the team
        expertise (List[str]): Areas of expertise for the team
        lead_agent: Optional lead agent for the team
        member_agents (List[Dict]): Agents with their roles in the team
        shared_resources (Dict[str, Any]): Resources available to team members
        team_memory (Dict[str, Any]): Shared memory accessible to all team members
    
    Example:
        ```python
        # Create a research team
        research_team = AgentTeam(
            name="Quantum Research Team",
            expertise=["quantum computing", "medical research", "data analysis"]
        )
        
        # Add agents with roles
        research_team.add_agent(researcher_agent, role="lead_researcher")
        research_team.add_agent(assistant_agent, role="research_assistant")
        research_team.add_agent(validator_agent, role="validation_specialist")
        ```
    """
    
    def __init__(
        self,
        name: str,
        expertise: List[str] = None,
        lead_agent = None,  # ContexaAgent
        team_id: str = None
    ):
        self.name = name
        self.expertise = expertise or []
        self.lead_agent = lead_agent
        self.member_agents = []
        self.shared_resources = {}
        self.team_memory = {}
        self.team_id = team_id or str(uuid.uuid4())
        
    def add_agent(self, agent, role: str = "member"):
        """Add an agent to the team
        
        Args:
            agent: The agent to add to the team
            role: The role the agent will play in the team
        """
        # Check if agent is already in the team
        for member in self.member_agents:
            if member["agent"].id == agent.id:
                # Update role if already a member
                member["role"] = role
                return
        
        # Add as new member
        self.member_agents.append({
            "agent": agent,
            "role": role,
            "joined_at": uuid.uuid1().hex
        })
        
        # Set up communication permissions if agent has the attribute
        if hasattr(agent, 'allowed_incoming_agents'):
            # Add all existing team members to agent's allowed list
            for member in self.member_agents:
                if member["agent"].id != agent.id:
                    agent.allowed_incoming_agents.append(member["agent"].id)
                    
                    # Also add this agent to other members' allowed lists
                    if hasattr(member["agent"], 'allowed_incoming_agents'):
                        member["agent"].allowed_incoming_agents.append(agent.id)
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the team
        
        Args:
            agent_id: ID of the agent to remove
            
        Returns:
            True if the agent was removed, False if not found
        """
        for i, member in enumerate(self.member_agents):
            if member["agent"].id == agent_id:
                # Remove from team
                removed_agent = self.member_agents.pop(i)
                
                # Update communication permissions
                for remaining in self.member_agents:
                    if hasattr(remaining["agent"], 'allowed_incoming_agents'):
                        # Remove the leaving agent from allowed lists
                        if agent_id in remaining["agent"].allowed_incoming_agents:
                            remaining["agent"].allowed_incoming_agents.remove(agent_id)
                
                return True
        
        return False
    
    def get_agents_by_role(self, role: str) -> List:
        """Get all agents with a specific role
        
        Args:
            role: The role to filter by
            
        Returns:
            List of agents with the specified role
        """
        matching = []
        for member in self.member_agents:
            if member["role"] == role:
                matching.append(member["agent"])
        
        return matching
    
    def assign_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Assign a task to this team
        
        Args:
            task: Task description and data
            
        Returns:
            Result of the task execution
            
        Notes:
            This is a high-level method that can be implemented differently
            depending on team coordination patterns
        """
        if self.lead_agent:
            # Leader delegates subtasks to team members
            return self.lead_agent.run({
                "task": task,
                "available_agents": [
                    {
                        "id": a["agent"].id,
                        "name": a["agent"].name,
                        "role": a["role"],
                        "expertise": getattr(a["agent"], "expertise", [])
                    } for a in self.member_agents
                ],
                "action": "delegate_task"
            })
        else:
            # Without a leader, assign to the most suitable agent
            suitable_agent = self._find_suitable_agent(task)
            return suitable_agent.run(task)
    
    def _find_suitable_agent(self, task: Dict[str, Any]):
        """Find the most suitable agent for a task
        
        This is a simplified implementation. In a production system,
        this would use more sophisticated matching logic.
        """
        # Default to first agent if no better match
        if not self.member_agents:
            raise ValueError("No agents in the team")
            
        return self.member_agents[0]["agent"] 