"""CrewAI adapter components for Contexa SDK.

This module provides functions to convert between Contexa objects and CrewAI objects,
as well as utilities for CrewAI orchestration.
"""

# Import CrewAI adapter functions from the main module
from contexa_sdk.adapters.crewai import (
    tool,
    model,
    agent,
    prompt,
    handoff,
)

# Import orchestration conversion functions
try:
    from contexa_sdk.adapters.crewai.orchestration import (
        agent_team_to_crew,
        task_handoff_to_crewai_task,
        adapt_crew_to_agent_team,
    )
    has_orchestration = True
except ImportError:
    has_orchestration = False

__all__ = [
    "tool",
    "model",
    "agent",
    "prompt",
    "handoff",
]

# Add orchestration functions if available
if has_orchestration:
    __all__.extend([
        "agent_team_to_crew",
        "task_handoff_to_crewai_task",
        "adapt_crew_to_agent_team",
    ]) 