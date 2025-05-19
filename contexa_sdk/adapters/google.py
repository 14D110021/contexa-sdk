"""
Google adapter for converting Contexa objects to Google GenAI SDK objects.

This file re-exports the functions from contexa_sdk.adapters.google_adk module
for backward compatibility and to provide a consistent interface.
"""

from contexa_sdk.adapters.google_adk import (
    tool,
    model,
    agent,
    prompt,
    handoff,
)

__all__ = [
    'tool',
    'model',
    'agent',
    'prompt',
    'handoff',
] 