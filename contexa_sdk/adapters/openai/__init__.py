"""OpenAI adapter components for Contexa SDK.

This module provides functions to convert between Contexa objects and OpenAI objects,
as well as utilities for managing OpenAI threads and assistants.
"""

from contexa_sdk.adapters.openai.thread import (
    get_thread_for_agent,
    memory_to_thread,
    thread_to_memory,
    handoff_to_thread,
    ThreadManager,
)

__all__ = [
    "get_thread_for_agent",
    "memory_to_thread",
    "thread_to_memory",
    "handoff_to_thread",
    "ThreadManager",
] 