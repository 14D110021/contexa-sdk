"""OpenAI adapter components for Contexa SDK.

This module provides functions to convert between Contexa objects and OpenAI objects,
as well as utilities for managing OpenAI threads and assistants.
"""

from contexa_sdk.adapters.openai_utils.thread import (
    get_thread_for_agent,
    memory_to_thread,
    thread_to_memory,
    handoff_to_thread,
    ThreadManager,
)

# Import the main adapter functions from the parent openai.py file
import sys
import os

# Add the parent directory to the path to import from openai.py
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    # Import directly from the openai.py file
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "openai_adapter", 
        os.path.join(parent_dir, "openai.py")
    )
    if spec and spec.loader:
        openai_adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(openai_adapter)
        
        tool = openai_adapter.tool
        model = openai_adapter.model
        agent = openai_adapter.agent
        prompt = openai_adapter.prompt
        adapt_assistant = openai_adapter.adapt_assistant
        adapt_agent = openai_adapter.adapt_agent
        handoff = openai_adapter.handoff
    else:
        raise ImportError("Could not load openai.py adapter")
        
except Exception as e:
    # Fallback: create placeholder functions
    print(f"Warning: Could not import OpenAI adapter functions: {e}")
    
    def tool(*args, **kwargs):
        raise ImportError("OpenAI adapter not properly loaded")
    
    def model(*args, **kwargs):
        raise ImportError("OpenAI adapter not properly loaded")
    
    def agent(*args, **kwargs):
        raise ImportError("OpenAI adapter not properly loaded")
    
    def prompt(*args, **kwargs):
        raise ImportError("OpenAI adapter not properly loaded")
    
    def adapt_assistant(*args, **kwargs):
        raise ImportError("OpenAI adapter not properly loaded")
    
    def adapt_agent(*args, **kwargs):
        raise ImportError("OpenAI adapter not properly loaded")
    
    def handoff(*args, **kwargs):
        raise ImportError("OpenAI adapter not properly loaded")

__all__ = [
    "get_thread_for_agent",
    "memory_to_thread",
    "thread_to_memory",
    "handoff_to_thread",
    "ThreadManager",
    "tool",
    "model", 
    "agent",
    "prompt",
    "adapt_assistant",
    "adapt_agent",
    "handoff",
] 