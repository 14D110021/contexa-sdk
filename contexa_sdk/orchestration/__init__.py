"""
Multi-agent orchestration package for Contexa SDK.

This package provides components for organizing, coordinating, and managing
interactions between multiple agents in collaborative workflows.
"""

from contexa_sdk.orchestration.message import Message, Channel
from contexa_sdk.orchestration.handoff import HandoffProtocol, TaskHandoff
from contexa_sdk.orchestration.workspace import SharedWorkspace, Artifact
from contexa_sdk.orchestration.team import AgentTeam

__all__ = [
    'Message',
    'Channel',
    'HandoffProtocol',
    'TaskHandoff',
    'SharedWorkspace',
    'Artifact',
    'AgentTeam'
] 