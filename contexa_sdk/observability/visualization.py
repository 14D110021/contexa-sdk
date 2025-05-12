"""
Agent Visualization Module for Contexa SDK.

This module provides functionality to visualize agent relationships,
tools, and handoffs using Graphviz. It helps developers understand
the structure and flow of their multi-agent systems through visual graphs.

Usage examples:
    ```python
    # Basic visualization
    from contexa_sdk.observability import draw_graph
    
    # Create a graph and display it
    graph = draw_graph(my_agent)
    
    # Save graph to file
    draw_graph(my_agent, filename="my_agent_graph")
    
    # Customize appearance
    draw_graph(my_agent, theme="dark", format="svg")
    
    # Create team visualization
    from contexa_sdk.observability import get_agent_team_graph
    get_agent_team_graph([agent1, agent2, agent3], team_name="My Team")
    
    # Export for web visualization
    from contexa_sdk.observability import export_graph_to_json
    graph_data = export_graph_to_json(my_agent, filename="agent_graph.json")
    ```
"""

import json
from typing import Dict, List, Optional, Set, Union, Any, Tuple
import importlib.util
import logging
import os

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import ContexaTool

logger = logging.getLogger(__name__)

def _check_graphviz_installed() -> bool:
    """
    Check if Graphviz Python package is installed.
    
    This is an internal helper function that verifies the availability
    of the graphviz package which is required for visualization.
    
    Returns:
        bool: True if graphviz is installed, False otherwise.
    """
    try:
        spec = importlib.util.find_spec("graphviz")
        return spec is not None
    except (ImportError, AttributeError):
        return False

def draw_graph(
    agent: ContexaAgent,
    include_tools: bool = True,
    include_handoffs: bool = True,
    filename: Optional[str] = None,
    format: str = "png",
    show_labels: bool = True,
    theme: str = "light",
) -> Any:
    """
    Generate a visualization of agent relationships, tools, and handoffs.
    
    This function creates a directed graph visualization where:
    - Agents are represented as yellow rectangles
    - Tools are represented as green ellipses
    - Handoffs are shown as solid arrows between agents
    - Tool usage is shown as dotted arrows
    
    The graph includes a start node and an end node to indicate the flow
    direction. If a filename is provided, the graph will be saved to disk.
    
    Args:
        agent: The root agent to visualize. All tools and handoffs
              associated with this agent (and any sub-agents) will be included.
        include_tools: If True (default), show tools associated with each agent.
                       Set to False for a cleaner graph focused only on agent relationships.
        include_handoffs: If True (default), show handoffs between agents.
                          This includes both static handoffs defined in the agent's
                          handoffs attribute and runtime handoffs recorded in the agent's memory.
        filename: Optional path to save the graph to. If provided, the graph will be
                 saved with the specified format extension. If not provided, the
                 graph will only be returned but not saved to disk.
        format: Output format for the graph file. Options include "png" (default),
                "svg", "pdf", "jpg", etc. For all supported formats, see Graphviz documentation.
        show_labels: If True (default), show descriptive labels on edges.
                     If False, edges will be shown without labels for a cleaner look.
        theme: Visual theme, either "light" (default) or "dark".
               Light theme has a white background, dark theme has a dark background.
        
    Returns:
        A Graphviz Digraph object that can be displayed, saved or further modified.
        
    Raises:
        ImportError: If graphviz package is not installed.
    
    Example:
        ```python
        # Basic usage
        from contexa_sdk.observability import draw_graph
        
        # Create and save a simple graph
        graph = draw_graph(my_agent, filename="agent_graph")
        
        # Customize the appearance
        dark_graph = draw_graph(
            agent=my_agent,
            theme="dark",
            format="svg",
            filename="agent_dark",
            show_labels=False  # Cleaner look without labels
        )
        
        # Generate a graph focusing only on agents (no tools)
        agents_only = draw_graph(my_agent, include_tools=False)
        ```
    """
    if not _check_graphviz_installed():
        raise ImportError(
            "Graphviz is required for visualization. "
            "Install with `pip install graphviz` or `pip install contexa-sdk[viz]`."
        )
    
    # Import here to avoid dependency issues
    from graphviz import Digraph
    
    # Define color schemes based on theme
    if theme == "dark":
        bg_color = "#2e2e2e"
        agent_fill = "#f1c40f"  # Yellow for agents
        agent_color = "#000000"
        tool_fill = "#2ecc71"   # Green for tools
        tool_color = "#000000"
        edge_color = "#ffffff"
        text_color = "#ffffff"
    else:  # light theme (default)
        bg_color = "#ffffff"
        agent_fill = "#f1c40f"  # Yellow for agents
        agent_color = "#000000"
        tool_fill = "#2ecc71"   # Green for tools
        tool_color = "#000000"
        edge_color = "#2c3e50"
        text_color = "#2c3e50"
    
    # Create a directed graph
    graph = Digraph(
        comment=f"Agent Graph for {agent.name}",
        format=format,
        node_attr={'style': 'filled', 'fontname': 'Arial'},
        edge_attr={'fontname': 'Arial', 'color': edge_color, 'fontcolor': text_color},
        graph_attr={'bgcolor': bg_color, 'fontcolor': text_color, 'fontname': 'Arial'},
    )
    
    # Add start node
    graph.node('__start__', 'Start', shape='oval', fillcolor='#3498db', fontcolor='white')
    
    # Process all agents and their connections
    processed_agents: Set[str] = set()
    processed_tools: Set[str] = set()
    
    def process_agent(a: ContexaAgent, parent_id: Optional[str] = None) -> None:
        """Process an agent and add it to the graph with its connections."""
        agent_id = f"agent_{id(a)}"
        
        if agent_id in processed_agents:
            # Already processed this agent
            if parent_id and show_labels:
                graph.edge(parent_id, agent_id, label="handoff", style='solid')
            return
        
        # Add agent node
        agent_label = f"{a.name}\n({a.description or ''})" if a.description else a.name
        graph.node(
            agent_id, 
            agent_label, 
            shape='box', 
            fillcolor=agent_fill,
            fontcolor=agent_color
        )
        processed_agents.add(agent_id)
        
        # Add edge from parent if this is a handoff
        if parent_id and show_labels:
            graph.edge(parent_id, agent_id, label="handoff", style='solid')
        elif parent_id:
            graph.edge(parent_id, agent_id, style='solid')
        elif parent_id is None:
            # This is the root agent, connect from start
            graph.edge('__start__', agent_id)
        
        # Add tools if requested
        if include_tools and hasattr(a, 'tools') and a.tools:
            for tool in a.tools:
                tool_id = f"tool_{id(tool)}"
                if tool_id not in processed_tools:
                    # Get tool name and description
                    tool_name = getattr(tool, 'name', getattr(tool, '__name__', str(tool)))
                    tool_desc = getattr(tool, 'description', '')
                    tool_label = f"{tool_name}\n({tool_desc})" if tool_desc else tool_name
                    
                    # Add tool node
                    graph.node(
                        tool_id, 
                        tool_label, 
                        shape='ellipse', 
                        fillcolor=tool_fill,
                        fontcolor=tool_color
                    )
                    processed_tools.add(tool_id)
                
                # Add edge from agent to tool
                if show_labels:
                    graph.edge(agent_id, tool_id, label="tool", style='dashed')
                else:
                    graph.edge(agent_id, tool_id, style='dashed')
        
        # Process handoffs if requested
        if include_handoffs:
            # First check for handoffs attribute (direct handoffs)
            handoffs = getattr(a, 'handoffs', [])
            for target in handoffs:
                if isinstance(target, ContexaAgent):
                    process_agent(target, agent_id)
            
            # Check for runtime handoffs (from memory/history)
            if hasattr(a, 'memory') and hasattr(a.memory, 'get_handoffs'):
                handoff_data = a.memory.get_handoffs()
                for handoff in handoff_data:
                    if hasattr(handoff, 'target_agent') and isinstance(handoff.target_agent, ContexaAgent):
                        process_agent(handoff.target_agent, agent_id)
    
    # Start processing from the root agent
    process_agent(agent)
    
    # Add end node
    graph.node('__end__', 'End', shape='oval', fillcolor='#e74c3c', fontcolor='white')
    
    # Connect leaf agents to end node
    for agent_id in processed_agents:
        # Check if this is a leaf node (no outgoing edges to other agents)
        has_outgoing = False
        for edge in graph.body:
            if edge.startswith(f'{agent_id} ->') and '->' not in edge.split('->')[1]:
                has_outgoing = True
                break
        
        if not has_outgoing:
            graph.edge(agent_id, '__end__')
    
    # Save the graph if a filename is provided
    if filename:
        graph.render(filename, cleanup=True)
    
    return graph

def get_agent_team_graph(
    agents: List[ContexaAgent],
    team_name: str = "Agent Team",
    **kwargs
) -> Any:
    """
    Generate a visualization of a team of agents.
    
    This is a convenience function that creates a temporary "team" agent
    with handoffs to all the agents in the list, then generates a visualization.
    This is useful when you have multiple independent agents that you want to
    visualize together but aren't naturally connected through handoffs.
    
    Args:
        agents: List of agents in the team. All agents in this list will appear
               in the graph connected to a central team node.
        team_name: Name for the team node in the graph. Defaults to "Agent Team".
        **kwargs: Additional arguments to pass to draw_graph, such as:
                 - filename: to save the graph
                 - format: output format (png, svg, etc.)
                 - theme: "light" or "dark"
                 - show_labels: whether to show edge labels
                 - include_tools: whether to include tool nodes
    
    Returns:
        A Graphviz Digraph object representing the team.
    
    Raises:
        ImportError: If graphviz is not installed.
    
    Example:
        ```python
        # Create a team visualization
        from contexa_sdk.observability import get_agent_team_graph
        
        # Define a list of agents
        research_team = [researcher, analyst, writer]
        
        # Generate and save the team graph
        team_graph = get_agent_team_graph(
            agents=research_team,
            team_name="Research Team",
            filename="research_team_graph",
            format="svg",
            theme="dark"
        )
        ```
    """
    if not _check_graphviz_installed():
        raise ImportError(
            "Graphviz is required for visualization. "
            "Install with `pip install graphviz` or `pip install contexa-sdk[viz]`."
        )
    
    # Import here to avoid dependency issues
    from graphviz import Digraph
    
    # Create a wrapper agent to contain the team
    root_agent = ContexaAgent(
        name=team_name,
        description="A team of agents",
        handoffs=agents
    )
    
    return draw_graph(root_agent, **kwargs)

def export_graph_to_json(
    agent: ContexaAgent,
    include_tools: bool = True,
    include_handoffs: bool = True,
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Export agent graph structure to JSON format for web visualization.
    
    This function generates a JSON representation of the agent graph structure,
    which can be used with frontend visualization libraries like D3.js, Cytoscape.js,
    or custom web-based graph visualizations. The JSON contains lists of nodes and edges
    with their properties.
    
    The exported structure includes:
    - Nodes: agents, tools, and control nodes (start/end)
    - Edges: connections between nodes (handoffs, tool usage, control flow)
    - Node properties: id, label, description, type
    - Edge properties: id, source, target, type
    
    Args:
        agent: The root agent to visualize. All tools and handoffs associated
              with this agent (and any sub-agents) will be included.
        include_tools: If True (default), include tool nodes in the exported graph.
                       Set to False for agent-only visualization.
        include_handoffs: If True (default), include handoff relationships.
                          This includes both static handoffs defined in the agent's
                          handoffs attribute and runtime handoffs recorded in memory.
        filename: Optional path to save the JSON to. If provided, the structure will be
                 saved as a JSON file. If not provided, the structure is only returned.
    
    Returns:
        A dictionary with the graph structure containing:
        - 'nodes': List of node objects
        - 'edges': List of edge objects
    
    Example:
        ```python
        from contexa_sdk.observability import export_graph_to_json
        
        # Export for web visualization
        graph_data = export_graph_to_json(
            agent=my_complex_agent,
            filename="agent_graph.json"
        )
        
        # Access the data structure
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]
        
        # Example: Count agent nodes
        agent_count = sum(1 for node in nodes if node["type"] == "agent")
        print(f"Graph contains {agent_count} agents")
        
        # Web integration example (JavaScript pseudocode):
        # fetch('agent_graph.json')
        #   .then(response => response.json())
        #   .then(data => {
        #     createVisualization(data.nodes, data.edges);
        #   });
        ```
    """
    nodes = []
    edges = []
    
    processed_agents = set()
    processed_tools = set()
    
    def process_agent(a: ContexaAgent, parent_id: Optional[str] = None) -> str:
        """Process an agent and add it to the graph structure."""
        agent_id = f"agent_{id(a)}"
        
        if agent_id in processed_agents:
            # Already processed this agent
            if parent_id:
                edges.append({
                    "id": f"edge_{parent_id}_{agent_id}",
                    "source": parent_id,
                    "target": agent_id,
                    "type": "handoff"
                })
            return agent_id
        
        # Add agent node
        nodes.append({
            "id": agent_id,
            "label": a.name,
            "description": a.description or "",
            "type": "agent"
        })
        processed_agents.add(agent_id)
        
        # Add edge from parent if this is a handoff
        if parent_id:
            edges.append({
                "id": f"edge_{parent_id}_{agent_id}",
                "source": parent_id,
                "target": agent_id,
                "type": "handoff"
            })
        
        # Add tools if requested
        if include_tools and hasattr(a, 'tools') and a.tools:
            for tool in a.tools:
                tool_id = f"tool_{id(tool)}"
                if tool_id not in processed_tools:
                    # Get tool name and description
                    tool_name = getattr(tool, 'name', getattr(tool, '__name__', str(tool)))
                    tool_desc = getattr(tool, 'description', '')
                    
                    # Add tool node
                    nodes.append({
                        "id": tool_id,
                        "label": tool_name,
                        "description": tool_desc,
                        "type": "tool"
                    })
                    processed_tools.add(tool_id)
                
                # Add edge from agent to tool
                edges.append({
                    "id": f"edge_{agent_id}_{tool_id}",
                    "source": agent_id,
                    "target": tool_id,
                    "type": "tool"
                })
        
        # Process handoffs if requested
        if include_handoffs:
            # First check for handoffs attribute (direct handoffs)
            handoffs = getattr(a, 'handoffs', [])
            for target in handoffs:
                if isinstance(target, ContexaAgent):
                    process_agent(target, agent_id)
            
            # Check for runtime handoffs (from memory/history)
            if hasattr(a, 'memory') and hasattr(a.memory, 'get_handoffs'):
                handoff_data = a.memory.get_handoffs()
                for handoff in handoff_data:
                    if hasattr(handoff, 'target_agent') and isinstance(handoff.target_agent, ContexaAgent):
                        process_agent(handoff.target_agent, agent_id)
        
        return agent_id
    
    # Start processing from the root agent
    start_node_id = "start"
    nodes.append({"id": start_node_id, "label": "Start", "type": "control"})
    
    agent_id = process_agent(agent)
    edges.append({
        "id": f"edge_{start_node_id}_{agent_id}",
        "source": start_node_id,
        "target": agent_id,
        "type": "control"
    })
    
    # Add end node
    end_node_id = "end"
    nodes.append({"id": end_node_id, "label": "End", "type": "control"})
    
    # Connect leaf agents to end node
    for node in nodes:
        if node["type"] != "agent":
            continue
            
        # Check if this is a leaf node (no outgoing edges to other agents)
        has_outgoing = False
        for edge in edges:
            if edge["source"] == node["id"] and edge["type"] == "handoff":
                has_outgoing = True
                break
        
        if not has_outgoing:
            edges.append({
                "id": f"edge_{node['id']}_{end_node_id}",
                "source": node["id"],
                "target": end_node_id,
                "type": "control"
            })
    
    graph_data = {
        "nodes": nodes,
        "edges": edges
    }
    
    # Save the graph if a filename is provided
    if filename:
        with open(filename, 'w') as f:
            json.dump(graph_data, f, indent=2)
    
    return graph_data 