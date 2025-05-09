"""OpenAI adapter for Contexa SDK.

This module provides adapters for converting between Contexa SDK and OpenAI
components, enabling interoperability between the two frameworks.
"""

from contexa_sdk.adapters.openai.converter import (
    convert_tool_to_openai,
    convert_model_to_openai,
    convert_agent_to_openai,
    adapt_openai_assistant,
)

__all__ = [
    "convert_tool_to_openai",
    "convert_model_to_openai",
    "convert_agent_to_openai",
    "adapt_openai_assistant",
] 