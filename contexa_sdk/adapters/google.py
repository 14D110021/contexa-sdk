"""
Google adapters for Contexa SDK.

This file re-exports functions from both the Google GenAI (google/genai.py) and
Google ADK (google/adk.py) adapter modules to provide a consistent interface.

For Google Generative AI (Palm/Gemini) use the genai_* functions.
For Google Agent Development Kit (ADK) use the adk_* functions.
"""

# Import GenAI adapter functions directly from genai.py
from contexa_sdk.adapters.google.genai import (
    tool as genai_tool,
    model as genai_model,
    agent as genai_agent,
    prompt as genai_prompt,
    handoff as genai_handoff,
)

# Import ADK adapter functions
from contexa_sdk.adapters.google.adk import (
    sync_adapt_agent as adk_agent,
    sync_handoff as adk_handoff,
)

from contexa_sdk.adapters.google.converter import (
    convert_tool as adk_tool,
    convert_model as adk_model,
)

# Define ADK prompt function for consistency
def adk_prompt(prompt):
    """Not fully implemented for ADK yet."""
    return str(prompt)

# For backward compatibility, default to GenAI
tool = genai_tool
model = genai_model
agent = genai_agent
prompt = genai_prompt
handoff = genai_handoff

__all__ = [
    # GenAI functions
    'genai_tool',
    'genai_model',
    'genai_agent',
    'genai_prompt',
    'genai_handoff',
    
    # ADK functions
    'adk_tool',
    'adk_model',
    'adk_agent',
    'adk_prompt',
    'adk_handoff',
    
    # Default functions (GenAI)
    'tool',
    'model',
    'agent',
    'prompt',
    'handoff',
] 