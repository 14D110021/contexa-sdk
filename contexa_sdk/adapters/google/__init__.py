"""Google adapters for Contexa SDK.

This module provides adapters for converting between Contexa SDK and Google AI 
components, enabling interoperability with:
1. Google Generative AI SDK (GenAI) - For working with Gemini models
2. Google Agent Development Kit (ADK) - For building agents using Google's ADK
"""

# Import Google GenAI adapter functions
from contexa_sdk.adapters.google.genai import (
    tool as genai_tool,
    model as genai_model,
    agent as genai_agent,
    prompt as genai_prompt,
    handoff as genai_handoff,
)

# Import Google ADK adapter functions
from contexa_sdk.adapters.google.adk import (
    sync_adapt_agent as adk_agent,
    sync_adapt_adk_agent as adk_adapt_agent,
    sync_handoff as adk_handoff,
)

# Import ADK converter functions
from contexa_sdk.adapters.google.converter import (
    convert_tool as adk_tool,
    convert_model as adk_model,
    convert_agent,
    adapt_agent,
    handoff as adk_converter_handoff,
)

# Define ADK prompt function for consistency with GenAI adapter
def adk_prompt(prompt):
    """Not fully implemented for ADK yet."""
    return str(prompt)

# Backward compatibility aliases - Using the GenAI implementations as defaults
tool = genai_tool
model = genai_model
agent = genai_agent
prompt = genai_prompt
handoff = genai_handoff

# Backward compatibility aliases
handoff_to_google_agent = adk_converter_handoff
convert_tool_to_google = adk_tool
convert_model_to_google = adk_model

__all__ = [
    # GenAI functions
    "genai_tool",
    "genai_model",
    "genai_agent",
    "genai_prompt",
    "genai_handoff",
    
    # ADK functions
    "adk_tool",
    "adk_model",
    "adk_agent",
    "adk_prompt",
    "adk_handoff",
    "adk_adapt_agent",
    
    # ADK compatibility functions
    "convert_tool_to_google",
    "convert_model_to_google",
    "convert_agent",
    "adapt_agent",
    "handoff_to_google_agent",
    
    # Default exports (using GenAI implementations)
    "tool",
    "model", 
    "agent",
    "prompt",
    "handoff",
] 