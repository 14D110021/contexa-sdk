"""CrewAI adapter for Contexa SDK.

This module provides adapters for converting between Contexa SDK and CrewAI
components, enabling interoperability between the two frameworks.
"""

from contexa_sdk.adapters.crewai.converter import (
    convert_tool_to_crewai,
    convert_model_to_crewai,
    convert_agent_to_crewai,
    adapt_crewai_agent,
)

__all__ = [
    "convert_tool_to_crewai",
    "convert_model_to_crewai",
    "convert_agent_to_crewai",
    "adapt_crewai_agent",
] 