"""LangGraph workflow support for LangChain integration.

This module provides conversion functions between Contexa orchestration objects and 
LangGraph workflow objects, enabling sophisticated agent workflows.
"""

import asyncio
from typing import Any, Dict, List, Callable, Optional, Union, Type

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.orchestration import AgentTeam, TaskHandoff


class LangGraphConverter:
    """Converter between Contexa orchestration and LangGraph workflows."""
    
    def __init__(self):
        """Initialize the LangGraph converter."""
        self._check_langgraph_available()
    
    def _check_langgraph_available(self):
        """Check if LangGraph is available."""
        try:
            import langgraph.graph
        except ImportError:
            raise ImportError(
                "LangGraph not found. Install with `pip install langgraph`."
            )
    
    def agent_team_to_graph(self, team: AgentTeam) -> Any:
        """Convert a Contexa AgentTeam to a LangGraph State Graph.
        
        Args:
            team: The Contexa AgentTeam to convert
            
        Returns:
            A LangGraph StateGraph
        """
        import langgraph.graph as lg
        from langgraph.graph import StateGraph
        
        # Create a state schema based on the team
        # The state will include all agents and their states
        class TeamState(lg.TypedDict):
            messages: List[Dict[str, Any]]  # Conversation history
            current_agent: str  # Currently active agent
            agents: Dict[str, Any]  # Agent states
            artifacts: Dict[str, Any]  # Shared artifacts/outputs
            
        # Create a new state graph
        workflow = StateGraph(TeamState)
        
        # Add nodes for each agent in the team
        for agent_id, agent_info in team.agents.items():
            agent = agent_info["agent"]
            
            # Create a node function that will run the agent
            async def agent_node(state: Dict[str, Any], agent=agent):
                # Extract the latest message from the conversation
                latest_msg = state["messages"][-1] if state["messages"] else {"content": ""}
                query = latest_msg.get("content", "")
                
                # Run the agent
                response = await agent.run(query)
                
                # Update the state
                return {
                    "messages": state["messages"] + [{"role": "assistant", "content": response}],
                    "current_agent": state["current_agent"],
                    "agents": state["agents"],
                    "artifacts": state["artifacts"]
                }
            
            # Convert to sync function for compatibility
            def sync_agent_node(state):
                return asyncio.run(agent_node(state))
                
            # Add the node to the graph
            workflow.add_node(agent_id, sync_agent_node)
        
        # Add routing logic based on team structure and expertise
        def router(state: Dict[str, Any]) -> str:
            """Route to the next agent based on the current state."""
            # If no current agent, select the first one
            if not state["current_agent"]:
                # Find the agent with leadership role if available
                for agent_id, agent_info in team.agents.items():
                    if agent_info.get("role") == "lead":
                        return agent_id
                # Otherwise, just pick the first agent
                return next(iter(team.agents.keys()))
            
            # Get the current message
            if not state["messages"]:
                return state["current_agent"]  # Stay with current agent
                
            latest_msg = state["messages"][-1]
            
            # Check if the message contains a handoff directive
            content = latest_msg.get("content", "")
            for agent_id in team.agents:
                if f"@{agent_id}" in content or f"HANDOFF TO {agent_id}" in content.upper():
                    return agent_id
            
            # If no handoff directive, stay with current agent
            return state["current_agent"]
        
        # Add conditional edges
        for agent_id in team.agents:
            workflow.add_conditional_edges(
                agent_id,
                router,
                {agent_id2: agent_id2 for agent_id2 in team.agents}
            )
        
        # Set the entry point to the router
        workflow.set_entry_point(router)
        
        # Compile the graph
        return workflow.compile()
    
    def task_handoff_to_edge(self, handoff: TaskHandoff, graph: Any) -> Any:
        """Add a task handoff as an edge in a LangGraph.
        
        Args:
            handoff: The Contexa TaskHandoff to convert
            graph: The LangGraph to add the edge to
            
        Returns:
            The updated graph
        """
        # Get the source and target agent IDs
        source_id = handoff.sender.agent_id
        target_id = handoff.recipient.agent_id
        
        # Create a conditional function that will trigger when this handoff occurs
        def handoff_condition(state: Dict[str, Any]) -> bool:
            """Return True if the handoff should occur."""
            if not state["messages"]:
                return False
                
            latest_msg = state["messages"][-1]
            content = latest_msg.get("content", "")
            
            # Check if the content matches this handoff
            task_desc = handoff.task_description.lower()
            content_lower = content.lower()
            
            return (
                task_desc in content_lower or
                f"handoff to {target_id}" in content_lower or
                f"@{target_id}" in content_lower
            )
        
        # Add the conditional edge
        graph.add_conditional_edge(
            source_id,
            handoff_condition,
            target_id
        )
        
        return graph
    
    def orchestration_to_langgraph(self, team: AgentTeam) -> Any:
        """Convert a complete Contexa orchestration to a LangGraph workflow.
        
        Args:
            team: The Contexa AgentTeam including all orchestration components
            
        Returns:
            A compiled LangGraph ready for execution
        """
        # Start with the basic team graph
        graph = self.agent_team_to_graph(team)
        
        # Add handoffs as conditional edges
        for handoff in team.handoffs:
            graph = self.task_handoff_to_edge(handoff, graph)
        
        return graph


# Create a singleton converter
converter = LangGraphConverter()

# Export functions
def agent_team_to_graph(team: AgentTeam) -> Any:
    """Convert a Contexa AgentTeam to a LangGraph workflow."""
    return converter.agent_team_to_graph(team)

def task_handoff_to_edge(handoff: TaskHandoff, graph: Any) -> Any:
    """Add a task handoff as an edge in a LangGraph."""
    return converter.task_handoff_to_edge(handoff, graph)

def orchestration_to_langgraph(team: AgentTeam) -> Any:
    """Convert a complete Contexa orchestration to a LangGraph workflow."""
    return converter.orchestration_to_langgraph(team) 