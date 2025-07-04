"""
Framework adapters for Contexa SDK.

This package provides adapter modules for converting Contexa core objects
and orchestration components to and from various framework-specific objects.
"""

# Re-export the modules
__all__ = [
    'langchain',
    'crewai',
    'openai',
    'google',
]

# Import adapters (these are lazy-loaded to avoid dependencies)
try:
    from contexa_sdk.adapters import langchain
except ImportError:
    pass

try:
    from contexa_sdk.adapters import crewai
except ImportError:
    pass

try:
    # Import OpenAI adapter functions directly from openai_adapter
    import sys
    import types
    from contexa_sdk.adapters.openai_adapter import (
        tool as openai_tool,
        model as openai_model,
        agent as openai_agent,
        prompt as openai_prompt,
        handoff as openai_handoff,
        adapt_assistant as openai_adapt_assistant,
        adapt_agent as openai_adapt_agent,
        OpenAIAdapter,
        __adapter_version__ as openai_adapter_version
    )
    
    # Create an openai module
    openai = types.ModuleType('contexa_sdk.adapters.openai')
    
    # Add all the functions to the module
    openai.tool = openai_tool
    openai.model = openai_model
    openai.agent = openai_agent
    openai.prompt = openai_prompt
    openai.handoff = openai_handoff
    openai.adapt_assistant = openai_adapt_assistant
    openai.adapt_agent = openai_adapt_agent
    openai.OpenAIAdapter = OpenAIAdapter
    openai.__adapter_version__ = openai_adapter_version
    
    # Add the module to sys.modules
    sys.modules['contexa_sdk.adapters.openai'] = openai
except ImportError:
    pass

try:
    # Import Google functions
    import sys
    import types
    from contexa_sdk.adapters.google.genai import (
        tool as genai_tool,
        model as genai_model, 
        agent as genai_agent,
        prompt as genai_prompt,
        handoff as genai_handoff
    )
    
    from contexa_sdk.adapters.google.adk import (
        sync_adapt_agent as adk_agent,
        sync_adapt_adk_agent as adk_adapt_agent,
        sync_handoff as adk_handoff
    )
    
    from contexa_sdk.adapters.google.converter import (
        convert_tool as adk_tool,
        convert_model as adk_model
    )
    
    # Define ADK prompt function
    def adk_prompt(prompt):
        """Not fully implemented for ADK yet."""
        return str(prompt)
    
    # Create a module
    google = types.ModuleType('contexa_sdk.adapters.google')
    
    # Add all the functions to the module
    # GenAI functions
    google.genai_tool = genai_tool
    google.genai_model = genai_model
    google.genai_agent = genai_agent
    google.genai_prompt = genai_prompt
    google.genai_handoff = genai_handoff
    
    # ADK functions
    google.adk_tool = adk_tool
    google.adk_model = adk_model
    google.adk_agent = adk_agent
    google.adk_prompt = adk_prompt
    google.adk_handoff = adk_handoff
    
    # Default functions (using GenAI implementations)
    google.tool = genai_tool
    google.model = genai_model
    google.agent = genai_agent
    google.prompt = genai_prompt
    google.handoff = genai_handoff
    
    # Add the module to sys.modules
    sys.modules['contexa_sdk.adapters.google'] = google
except ImportError:
    pass 