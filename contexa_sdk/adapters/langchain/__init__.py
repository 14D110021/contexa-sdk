"""LangChain adapter components for Contexa SDK.

This module provides functions to convert between Contexa objects and LangChain objects,
as well as utilities for LangGraph workflow creation.
"""

from contexa_sdk.adapters.langchain.converter import (
    convert_tool_to_langchain,
    convert_model_to_langchain,
    convert_agent_to_langchain,
    adapt_langchain_agent,
)

# Import LangGraph conversion functions
try:
    from contexa_sdk.adapters.langchain.langgraph import (
        agent_team_to_graph,
        task_handoff_to_edge,
        orchestration_to_langgraph,
    )
    has_langgraph = True
except ImportError:
    has_langgraph = False

__all__ = [
    "convert_tool_to_langchain",
    "convert_model_to_langchain",
    "convert_agent_to_langchain",
    "adapt_langchain_agent",
]

# Add LangGraph functions if available
if has_langgraph:
    __all__.extend([
        "agent_team_to_graph",
        "task_handoff_to_edge",
        "orchestration_to_langgraph",
    ]) 