"""
Framework adapters for Contexa SDK.

This package provides adapter modules for converting Contexa core objects
and orchestration components to and from various framework-specific objects.
"""

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
    from contexa_sdk.adapters import openai
except ImportError:
    pass

try:
    from contexa_sdk.adapters import google
except ImportError:
    pass 