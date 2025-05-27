"""
MCP Capabilities system for server capability negotiation.

This module implements the capability negotiation system defined in the MCP
specification, allowing servers to declare their supported features and
clients to understand what functionality is available.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class MCPCapabilityType(Enum):
    """Types of MCP capabilities."""
    RESOURCES = "resources"
    TOOLS = "tools"
    PROMPTS = "prompts"
    SAMPLING = "sampling"
    ROOTS = "roots"
    LOGGING = "logging"


@dataclass
class ResourceCapability:
    """Resource capability configuration."""
    subscribe: bool = False
    list_changed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for capability negotiation."""
        return {
            "subscribe": self.subscribe,
            "listChanged": self.list_changed,
        }


@dataclass
class ToolCapability:
    """Tool capability configuration."""
    list_changed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for capability negotiation."""
        return {
            "listChanged": self.list_changed,
        }


@dataclass
class PromptCapability:
    """Prompt capability configuration."""
    list_changed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for capability negotiation."""
        return {
            "listChanged": self.list_changed,
        }


@dataclass
class SamplingCapability:
    """Sampling capability configuration."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for capability negotiation."""
        return {}


@dataclass
class RootsCapability:
    """Roots capability configuration."""
    list_changed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for capability negotiation."""
        return {
            "listChanged": self.list_changed,
        }


@dataclass
class LoggingCapability:
    """Logging capability configuration."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for capability negotiation."""
        return {}


@dataclass
class ServerCapabilities:
    """
    Server capabilities for MCP capability negotiation.
    
    This class manages the capabilities that an MCP server declares during
    the initialization handshake. Capabilities determine which protocol
    features are available during the session.
    """
    
    resources: Optional[ResourceCapability] = None
    tools: Optional[ToolCapability] = None
    prompts: Optional[PromptCapability] = None
    sampling: Optional[SamplingCapability] = None
    roots: Optional[RootsCapability] = None
    logging: Optional[LoggingCapability] = None
    
    # Custom capabilities for extensions
    experimental: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default capabilities if none provided."""
        if self.resources is None and self.tools is None and self.prompts is None:
            # Default to basic tool capability if nothing specified
            self.tools = ToolCapability()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert capabilities to dictionary for MCP negotiation.
        
        Returns:
            Dictionary representation suitable for MCP initialize response
        """
        capabilities = {}
        
        if self.resources is not None:
            capabilities["resources"] = self.resources.to_dict()
        
        if self.tools is not None:
            capabilities["tools"] = self.tools.to_dict()
        
        if self.prompts is not None:
            capabilities["prompts"] = self.prompts.to_dict()
        
        if self.sampling is not None:
            capabilities["sampling"] = self.sampling.to_dict()
        
        if self.roots is not None:
            capabilities["roots"] = self.roots.to_dict()
        
        if self.logging is not None:
            capabilities["logging"] = self.logging.to_dict()
        
        # Add experimental capabilities
        if self.experimental:
            capabilities["experimental"] = self.experimental
        
        return capabilities
    
    def has_capability(self, capability_type: MCPCapabilityType) -> bool:
        """Check if a specific capability is enabled."""
        capability_map = {
            MCPCapabilityType.RESOURCES: self.resources,
            MCPCapabilityType.TOOLS: self.tools,
            MCPCapabilityType.PROMPTS: self.prompts,
            MCPCapabilityType.SAMPLING: self.sampling,
            MCPCapabilityType.ROOTS: self.roots,
            MCPCapabilityType.LOGGING: self.logging,
        }
        
        return capability_map.get(capability_type) is not None
    
    def get_supported_methods(self) -> Set[str]:
        """Get the set of MCP methods supported by these capabilities."""
        methods = set()
        
        # Core methods always supported
        methods.update([
            "initialize",
            "ping",
        ])
        
        if self.resources is not None:
            methods.update([
                "resources/list",
                "resources/read",
            ])
            if self.resources.subscribe:
                methods.update([
                    "resources/subscribe",
                    "resources/unsubscribe",
                ])
        
        if self.tools is not None:
            methods.update([
                "tools/list",
                "tools/call",
            ])
        
        if self.prompts is not None:
            methods.update([
                "prompts/list",
                "prompts/get",
            ])
        
        if self.sampling is not None:
            methods.update([
                "sampling/createMessage",
            ])
        
        if self.roots is not None:
            methods.update([
                "roots/list",
            ])
        
        if self.logging is not None:
            methods.update([
                "logging/setLevel",
            ])
        
        return methods
    
    def validate_request_method(self, method: str) -> bool:
        """Validate that a request method is supported by current capabilities."""
        supported_methods = self.get_supported_methods()
        return method in supported_methods
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerCapabilities':
        """Create ServerCapabilities from dictionary."""
        kwargs = {}
        
        if "resources" in data:
            kwargs["resources"] = ResourceCapability(**data["resources"])
        
        if "tools" in data:
            kwargs["tools"] = ToolCapability(**data["tools"])
        
        if "prompts" in data:
            kwargs["prompts"] = PromptCapability(**data["prompts"])
        
        if "sampling" in data:
            kwargs["sampling"] = SamplingCapability(**data["sampling"])
        
        if "roots" in data:
            kwargs["roots"] = RootsCapability(**data["roots"])
        
        if "logging" in data:
            kwargs["logging"] = LoggingCapability(**data["logging"])
        
        if "experimental" in data:
            kwargs["experimental"] = data["experimental"]
        
        return cls(**kwargs)
    
    def merge_with_client_capabilities(
        self, 
        client_capabilities: Dict[str, Any]
    ) -> 'ServerCapabilities':
        """
        Merge server capabilities with client capabilities to determine
        the final negotiated capabilities for the session.
        
        Args:
            client_capabilities: Capabilities declared by the client
            
        Returns:
            New ServerCapabilities object with negotiated capabilities
        """
        # For now, we just return our own capabilities
        # In a more sophisticated implementation, we would negotiate
        # based on what both client and server support
        return self
    
    def create_capability_summary(self) -> Dict[str, Any]:
        """Create a human-readable summary of capabilities."""
        summary = {
            "supported_features": [],
            "method_count": len(self.get_supported_methods()),
            "methods": sorted(list(self.get_supported_methods())),
        }
        
        if self.resources is not None:
            summary["supported_features"].append("Resources")
            if self.resources.subscribe:
                summary["supported_features"].append("Resource Subscriptions")
        
        if self.tools is not None:
            summary["supported_features"].append("Tools")
        
        if self.prompts is not None:
            summary["supported_features"].append("Prompts")
        
        if self.sampling is not None:
            summary["supported_features"].append("Sampling")
        
        if self.roots is not None:
            summary["supported_features"].append("Roots")
        
        if self.logging is not None:
            summary["supported_features"].append("Logging")
        
        if self.experimental:
            summary["supported_features"].append("Experimental Features")
            summary["experimental_features"] = list(self.experimental.keys())
        
        return summary


def create_default_server_capabilities() -> ServerCapabilities:
    """Create default server capabilities for a basic MCP server."""
    return ServerCapabilities(
        tools=ToolCapability(list_changed=True),
        resources=ResourceCapability(subscribe=False, list_changed=True),
        prompts=PromptCapability(list_changed=True),
        logging=LoggingCapability(),
    )


def create_full_server_capabilities() -> ServerCapabilities:
    """Create full server capabilities with all features enabled."""
    return ServerCapabilities(
        resources=ResourceCapability(subscribe=True, list_changed=True),
        tools=ToolCapability(list_changed=True),
        prompts=PromptCapability(list_changed=True),
        sampling=SamplingCapability(),
        roots=RootsCapability(list_changed=True),
        logging=LoggingCapability(),
    ) 