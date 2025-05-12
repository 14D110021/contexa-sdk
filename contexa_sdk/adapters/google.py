"""
Google adapter for converting Contexa objects to Google GenAI SDK objects.

This file re-exports the functions from contexa_sdk.adapters.google module
for backward compatibility and to provide a consistent interface.
"""

from contexa_sdk.adapters.google import (
    convert_tool_to_google as tool,
    convert_model_to_google as model,
    convert_agent_to_google as agent,
    adapt_google_agent as adapt_agent,
)

__all__ = [
    'tool',
    'model',
    'agent',
    'adapt_agent',
] 