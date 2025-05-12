"""Google ADK adapter for Contexa SDK.

This module provides adapters for converting between Contexa SDK and Google ADK
components, enabling interoperability between the two frameworks.
"""

from contexa_sdk.adapters.google.converter import (
    convert_tool_to_google,
    convert_model_to_google,
    convert_agent_to_google,
    adapt_google_agent,
    handoff_to_google_agent,
    # Aliases for backward compatibility
    convert_tool,
    convert_model,
    convert_agent,
    adapt_agent,
)

# Export handoff as a separate function for clarity
handoff = handoff_to_google_agent

__all__ = [
    "convert_tool_to_google",
    "convert_model_to_google",
    "convert_agent_to_google",
    "adapt_google_agent",
    "convert_tool",
    "convert_model",
    "convert_agent",
    "adapt_agent",
    "handoff",
] 