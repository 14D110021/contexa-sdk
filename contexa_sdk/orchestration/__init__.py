"""
Multi-agent orchestration package for Contexa SDK.

This package provides components for organizing, coordinating, and managing
interactions between multiple agents in collaborative workflows.
"""

from contexa_sdk.orchestration.message import Message, Channel
from contexa_sdk.orchestration.handoff import HandoffProtocol, TaskHandoff
from contexa_sdk.orchestration.workspace import SharedWorkspace, Artifact
from contexa_sdk.orchestration.team import AgentTeam

# Import MCP components conditionally to avoid breaking existing code
try:
    from contexa_sdk.orchestration.mcp_agent import (
        MCPAgent, MessageEnvelope, AgentState, Registry, TaskBroker, registry, broker
    )
    from contexa_sdk.orchestration.mcp_handoff import (
        handoff as mcp_handoff, register_contexa_agent, MCPHandoff, MCPAdapterForContexaAgent
    )
    __mcp_available__ = True
except ImportError:
    __mcp_available__ = False

__all__ = [
    'Message',
    'Channel',
    'HandoffProtocol',
    'TaskHandoff',
    'SharedWorkspace',
    'Artifact',
    'AgentTeam'
]

# Add MCP components to __all__ if available
if __mcp_available__:
    __all__.extend([
        'MCPAgent',
        'MessageEnvelope',
        'AgentState',
        'Registry',
        'TaskBroker',
        'registry',
        'broker',
        'mcp_handoff',
        'register_contexa_agent',
        'MCPHandoff',
        'MCPAdapterForContexaAgent'
    ]) 