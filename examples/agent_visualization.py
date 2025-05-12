"""
Example demonstrating agent visualization in Contexa SDK.

This example shows how to:
1. Create a multi-agent system with tools and handoffs
2. Generate visualizations of the agent graph
3. Export the graph to different formats
4. Customize the graph appearance

The visualization helps in understanding the orchestration flow of agents,
tools they have access to, and how handoffs enable agent communication.
"""

import asyncio
import os
import sys
from typing import Dict, Any
from pathlib import Path

# Add the parent directory to the path so we can import the SDK
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.observability import draw_graph, get_agent_team_graph, export_graph_to_json


# Define some tools for our agents
@ContexaTool.register(
    name="search_knowledge_base",
    description="Search the internal knowledge base for information"
)
async def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for information."""
    # This is a simulated function
    return f"Knowledge base results for '{query}': Found relevant information."


@ContexaTool.register(
    name="analyze_data",
    description="Analyze data and generate insights"
)
async def analyze_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze data and generate insights."""
    # This is a simulated function
    return {
        "insights": f"Analysis of data with {len(data)} fields complete.",
        "recommendations": ["Recommendation 1", "Recommendation 2"]
    }


@ContexaTool.register(
    name="generate_report",
    description="Generate a formatted report"
)
async def generate_report(title: str, content: Dict[str, Any]) -> str:
    """Generate a formatted report."""
    # This is a simulated function
    return f"Report '{title}' generated with {len(content)} sections."


def create_agent_system():
    """
    Create a sample multi-agent system for visualization.
    
    This function creates a hierarchical agent system with:
    - An orchestrator agent at the top
    - Three specialized agents (researcher, analyst, report writer)
    - Each agent has specific tools for their tasks
    - Handoff relationships between agents
    
    Returns:
        Tuple of (orchestrator, researcher, analyst, report_writer) agents
    """
    print("\n🤖 Creating a multi-agent system...")
    
    # Create a model (we'll use the same for all agents in this example)
    model = ContexaModel(
        provider="openai",
        model_name="gpt-4-turbo"
    )
    
    # Create specialized agents
    researcher = ContexaAgent(
        name="Research Agent",
        description="Specializes in finding information from knowledge bases",
        model=model,
        tools=[search_knowledge_base],
        system_prompt="You are a research agent that finds relevant information."
    )
    
    analyst = ContexaAgent(
        name="Data Analyst",
        description="Analyzes data and generates insights",
        model=model,
        tools=[analyze_data],
        system_prompt="You are a data analyst that provides insights from data."
    )
    
    report_writer = ContexaAgent(
        name="Report Writer",
        description="Generates well-formatted reports",
        model=model,
        tools=[generate_report],
        system_prompt="You are a report writer that creates professional reports."
    )
    
    # Create an orchestrator agent that can hand off to the specialized agents
    orchestrator = ContexaAgent(
        name="Orchestrator",
        description="Coordinates tasks among specialized agents",
        model=model,
        handoffs=[researcher, analyst, report_writer],
        system_prompt=(
            "You are an orchestrator agent that coordinates tasks among specialized agents. "
            "Delegate research tasks to the Research Agent, data analysis to the Data Analyst, "
            "and report generation to the Report Writer."
        )
    )
    
    print("✅ Created a hierarchical agent system with orchestrator and 3 specialized agents")
    return orchestrator, researcher, analyst, report_writer


def basic_visualization(orchestrator, output_dir):
    """
    Example 1: Basic agent visualization
    
    This function demonstrates the simplest way to visualize an agent system:
    - Creates a basic graph with default settings
    - Saves it as a PNG file
    
    Args:
        orchestrator: The root orchestrator agent
        output_dir: Directory to save the visualization
    """
    print("\n📊 Example 1: Basic agent visualization")
    print("Generating a basic graph of the agent system...")
    
    try:
        # Draw the graph with default settings (PNG format, light theme)
        graph = draw_graph(
            orchestrator,
            filename=str(output_dir / "1_basic_graph")
        )
        print(f"✅ Basic graph saved to {output_dir}/1_basic_graph.png")
        print("   This graph shows:")
        print("   - Yellow rectangles: Agents")
        print("   - Green ellipses: Tools")
        print("   - Solid arrows: Handoff relationships")
        print("   - Dotted arrows: Tool usage")
    except ImportError as e:
        print(f"⚠️ {str(e)}")
        print("📝 Run: pip install contexa-sdk[viz] to enable visualization")
        return False
    
    return True


def custom_themed_visualization(orchestrator, output_dir):
    """
    Example 2: Customized visualization with dark theme
    
    This function demonstrates how to customize the visualization:
    - Uses dark theme for better visibility in dark environments
    - Outputs in SVG format for scalable graphics
    - Shows labels on the edges for better clarity
    
    Args:
        orchestrator: The root orchestrator agent
        output_dir: Directory to save the visualization
    """
    print("\n📊 Example 2: Customized dark theme visualization")
    print("Generating a customized graph with dark theme...")
    
    # Draw a customized graph
    graph = draw_graph(
        orchestrator,
        filename=str(output_dir / "2_dark_theme"),
        theme="dark",           # Dark background
        format="svg",           # Scalable Vector Graphics format
        show_labels=True        # Show labels on edges
    )
    print(f"✅ Dark theme graph saved to {output_dir}/2_dark_theme.svg")
    print("   This SVG file can be opened in any web browser and scales well")
    print("   The dark theme is better for presentations or dark mode interfaces")


def agents_only_visualization(orchestrator, output_dir):
    """
    Example 3: Agent-only visualization
    
    This function creates a simplified graph focusing only on agents:
    - Hides all tools for a cleaner view of agent relationships
    - Useful for understanding the high-level orchestration pattern
    
    Args:
        orchestrator: The root orchestrator agent
        output_dir: Directory to save the visualization
    """
    print("\n📊 Example 3: Agent-only visualization")
    print("Generating a simplified graph with only agents (no tools)...")
    
    # Draw an agent-only graph
    graph = draw_graph(
        orchestrator,
        filename=str(output_dir / "3_agents_only"),
        include_tools=False     # Hide tools for simplicity
    )
    print(f"✅ Agent-only graph saved to {output_dir}/3_agents_only.png")
    print("   This simplified view is clearer for understanding agent relationships")
    print("   Especially useful for complex systems with many tools")


def team_visualization(researcher, analyst, report_writer, output_dir):
    """
    Example 4: Team visualization
    
    This function demonstrates visualizing a team of independent agents:
    - Creates a team visualization with multiple agents
    - Useful for visualizing agent teams that aren't connected via handoffs
    
    Args:
        researcher, analyst, report_writer: Individual agents
        output_dir: Directory to save the visualization
    """
    print("\n📊 Example 4: Team visualization")
    print("Generating a team graph of the specialized agents...")
    
    # Create a team visualization
    team_graph = get_agent_team_graph(
        [researcher, analyst, report_writer],  # List of agents
        team_name="Analytics Team",            # Name for the team
        filename=str(output_dir / "4_team_graph")
    )
    print(f"✅ Team graph saved to {output_dir}/4_team_graph.png")
    print("   This graph shows all agents as part of a team")
    print("   The team visualization creates a virtual 'team agent' that connects to all members")


def json_export(orchestrator, output_dir):
    """
    Example 5: Export to JSON for web visualization
    
    This function exports the agent graph to JSON format:
    - Creates a structured JSON representation of the graph
    - Can be used with web visualization libraries
    
    Args:
        orchestrator: The root orchestrator agent
        output_dir: Directory to save the visualization
    """
    print("\n💾 Example 5: Export to JSON for web visualization")
    print("Exporting the graph structure to JSON format...")
    
    # Export to JSON format
    json_data = export_graph_to_json(
        orchestrator,
        filename=str(output_dir / "5_agent_graph.json")
    )
    print(f"✅ Graph data exported to {output_dir}/5_agent_graph.json")
    print(f"   JSON contains {len(json_data['nodes'])} nodes and {len(json_data['edges'])} edges")
    print("   This JSON can be visualized with libraries like D3.js or Cytoscape.js")
    print("   Example web usage:")
    print("   ```javascript")
    print("   fetch('5_agent_graph.json')")
    print("     .then(response => response.json())")
    print("     .then(data => {")
    print("       // Create visualization with D3.js or Cytoscape.js")
    print("       createVisualization(data.nodes, data.edges);")
    print("     });")
    print("   ```")


async def runtime_handoff_visualization(orchestrator, researcher, analyst, report_writer, output_dir):
    """
    Example 6: Runtime handoff visualization
    
    This function demonstrates visualizing runtime handoffs:
    - Simulates handoffs between agents during execution
    - Shows how the visualization captures actual communication flow
    
    Args:
        orchestrator, researcher, analyst, report_writer: The agents
        output_dir: Directory to save the visualization
    """
    print("\n🔄 Example 6: Runtime handoff visualization")
    print("Simulating runtime handoffs between agents...")
    
    # Simulate a series of handoffs
    print("   ➡️ Orchestrator → Researcher: 'Find information about renewable energy'")
    await orchestrator.handoff(
        target_agent=researcher,
        query="Find information about renewable energy",
        context={"purpose": "Market research"}
    )
    
    print("   ➡️ Researcher → Analyst: 'Analyze this renewable energy data'")
    await researcher.handoff(
        target_agent=analyst,
        query="Analyze this renewable energy data",
        context={"data": {"solar": 35, "wind": 42, "hydro": 18}}
    )
    
    print("   ➡️ Analyst → Report Writer: 'Generate a report on renewable energy findings'")
    await analyst.handoff(
        target_agent=report_writer,
        query="Generate a report on renewable energy findings",
        context={"analysis": {"insights": "Renewable energy growing at 15% annually"}}
    )
    
    # Visualize the graph with runtime handoffs
    print("\nGenerating graph showing the runtime handoffs...")
    runtime_graph = draw_graph(
        orchestrator, 
        filename=str(output_dir / "6_runtime_handoffs")
    )
    print(f"✅ Runtime handoffs graph saved to {output_dir}/6_runtime_handoffs.png")
    print("   This graph shows the actual flow of tasks during execution")
    print("   Note how it captures handoffs that happened at runtime, not just static definitions")


async def demonstrate_visualization():
    """Create a multi-agent system and visualize it."""
    print("🚀 Agent Visualization Example")
    
    # Create output directory if it doesn't exist
    output_dir = Path("./visualization_output")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Create the agent system
        orchestrator, researcher, analyst, report_writer = create_agent_system()
        
        # Example 1: Basic visualization
        if not basic_visualization(orchestrator, output_dir):
            # Exit if visualization dependencies are not installed
            return
        
        # Example 2: Customized dark theme
        custom_themed_visualization(orchestrator, output_dir)
        
        # Example 3: Agent-only visualization
        agents_only_visualization(orchestrator, output_dir)
        
        # Example 4: Team visualization
        team_visualization(researcher, analyst, report_writer, output_dir)
        
        # Example 5: JSON export for web visualization
        json_export(orchestrator, output_dir)
        
        # Example 6: Runtime handoff visualization
        await runtime_handoff_visualization(
            orchestrator, researcher, analyst, report_writer, output_dir
        )
        
        print("\n📝 To view all visualizations, check the visualization_output directory")
        print("✅ Agent visualization example completed")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(demonstrate_visualization()) 