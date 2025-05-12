"""Google ADK adapter for Contexa SDK.

This module provides adapters for converting between Contexa SDK and Google ADK
components, enabling interoperability between the two frameworks.
"""

from contexa_sdk.adapters.google.converter import (
    convert_tool_to_google,
    convert_model_to_google,
    convert_agent_to_google,
    adapt_google_agent,
)

__all__ = [
    "convert_tool_to_google",
    "convert_model_to_google",
    "convert_agent_to_google",
    "adapt_google_agent",
] 