"""Adapters for converting Contexa objects to framework-native objects."""

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
    from contexa_sdk.adapters import google_adk
except ImportError:
    pass 