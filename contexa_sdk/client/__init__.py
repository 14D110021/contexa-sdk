"""Client module for easy access to Contexa resources."""

from contexa_sdk.client.tools import ctx_tools
from contexa_sdk.client.models import ctx_model
from contexa_sdk.client.agents import ctx_agent
from contexa_sdk.client.registry import ResourceRegistry

# Create a global registry instance
registry = ResourceRegistry()

__all__ = [
    "ctx_tools",
    "ctx_model",
    "ctx_agent",
    "registry",
] 