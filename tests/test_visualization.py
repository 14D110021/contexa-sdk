"""Tests for the agent visualization module."""

import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool


class TestVisualization:
    """Tests for agent visualization functionality."""

    @pytest.fixture
    def sample_agent(self):
        """Create a sample agent for testing."""
        # Create a simple tool
        @ContexaTool.register(
            name="test_tool",
            description="A test tool"
        )
        async def test_tool(query: str) -> str:
            return f"Test result for {query}"
        
        # Create a model
        model = ContexaModel(
            provider="test",
            model_name="test-model"
        )
        
        # Create a child agent
        child_agent = ContexaAgent(
            name="Child Agent",
            description="A child agent",
            model=model,
            tools=[test_tool],
            system_prompt="You are a helpful child agent"
        )
        
        # Create the main agent
        agent = ContexaAgent(
            name="Main Agent",
            description="A main agent",
            model=model,
            tools=[test_tool],
            handoffs=[child_agent],
            system_prompt="You are a helpful main agent"
        )
        
        return agent

    @pytest.mark.skipif(
        not pytest.importorskip("graphviz", reason="graphviz not installed"),
        reason="graphviz not installed"
    )
    def test_draw_graph(self, sample_agent):
        """Test drawing an agent graph."""
        from contexa_sdk.observability.visualization import draw_graph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test_graph")
            graph = draw_graph(sample_agent, filename=filename)
            
            # Check that the graph was created
            assert os.path.exists(f"{filename}.png")
            
            # Check that the graph has the correct components
            assert "Main Agent" in graph.source
            assert "Child Agent" in graph.source
            assert "test_tool" in graph.source

    @pytest.mark.skipif(
        not pytest.importorskip("graphviz", reason="graphviz not installed"),
        reason="graphviz not installed"
    )
    def test_get_agent_team_graph(self, sample_agent):
        """Test creating a team graph."""
        from contexa_sdk.observability.visualization import get_agent_team_graph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "team_graph")
            
            # Create a team with multiple agents
            agents = [sample_agent]
            
            # Add another agent to the team
            new_agent = ContexaAgent(
                name="New Agent",
                description="Another agent",
                model=sample_agent.model,
                tools=[],
                system_prompt="You are another helpful agent"
            )
            agents.append(new_agent)
            
            # Generate the team graph
            graph = get_agent_team_graph(agents, team_name="Test Team", filename=filename)
            
            # Check that the graph was created
            assert os.path.exists(f"{filename}.png")
            
            # Check that the graph contains all agents
            assert "Main Agent" in graph.source
            assert "New Agent" in graph.source
            assert "Test Team" in graph.source

    def test_export_graph_to_json(self, sample_agent):
        """Test exporting a graph to JSON."""
        from contexa_sdk.observability.visualization import export_graph_to_json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "graph.json")
            
            # Export the graph to JSON
            graph_data = export_graph_to_json(sample_agent, filename=filename)
            
            # Check that the JSON file was created
            assert os.path.exists(filename)
            
            # Check that the graph data has the expected structure
            assert "nodes" in graph_data
            assert "edges" in graph_data
            
            # Verify nodes contain the agents and tools
            node_labels = [node["label"] for node in graph_data["nodes"]]
            assert "Main Agent" in node_labels
            assert "Child Agent" in node_labels
            assert "test_tool" in node_labels
            
            # Check that the JSON file contains the correct data
            with open(filename, "r") as f:
                file_data = json.load(f)
                assert file_data == graph_data

    def test_no_graphviz_installed(self):
        """Test behavior when graphviz is not installed."""
        with patch("importlib.util.find_spec", return_value=None):
            from contexa_sdk.observability.visualization import _check_graphviz_installed
            
            # Check that graphviz installation check returns False
            assert not _check_graphviz_installed()
            
            # Test that draw_graph raises ImportError
            from contexa_sdk.observability.visualization import draw_graph
            
            with pytest.raises(ImportError):
                draw_graph(MagicMock())

    def test_import_fallback(self):
        """Test the import fallback behavior in __init__.py."""
        # Mock the visualization import to raise ImportError
        with patch("contexa_sdk.observability.visualization", side_effect=ImportError):
            # Re-import to trigger the fallback
            import importlib
            import contexa_sdk.observability
            importlib.reload(contexa_sdk.observability)
            
            # Check that placeholder functions are created
            with pytest.raises(ImportError):
                contexa_sdk.observability.draw_graph("test") 