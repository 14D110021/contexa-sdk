"""Configuration for Contexa SDK.

This module provides the configuration system for the Contexa SDK, allowing users
to customize settings for API connections, timeouts, authentication, and other parameters.
The configuration can be passed to various core components like tools, agents,
and models to control their behavior.

Examples:
    Create and use a configuration:
    
    ```python
    from contexa_sdk.core.config import ContexaConfig
    
    # Create a configuration with custom settings
    config = ContexaConfig(
        api_key="your-api-key",
        timeout=30,
        metadata={"environment": "production"}
    )
    
    # Use the configuration with a tool or agent
    tool = ContexaTool(..., config=config)
    agent = ContexaAgent(..., config=config)
    ```
"""

from typing import Dict, Optional, Any
from pydantic import BaseModel, Field


class ContexaConfig(BaseModel):
    """Configuration for Contexa SDK.
    
    This class provides a unified configuration object that can be used across
    the SDK to control behavior of tools, agents, models, and other components.
    It includes settings for API connections, authentication, timeouts, and
    allows for custom metadata to be attached.
    
    The configuration uses Pydantic for validation and defaults, making it easy
    to serialize/deserialize and integrate with other systems.
    
    Attributes:
        api_key (Optional[str]): Contexa API key for authentication with cloud services
        api_url (str): Base URL for Contexa API endpoints
        org_id (Optional[str]): Organization ID for multi-tenant deployments
        timeout (int): Default timeout in seconds for network operations
        metadata (Dict[str, Any]): Arbitrary metadata for customizing component behavior
    """
    
    api_key: Optional[str] = Field(
        default=None, 
        description="Contexa API key for authentication"
    )
    api_url: str = Field(
        default="https://api.contexa.ai/v0", 
        description="Contexa API URL"
    )
    org_id: Optional[str] = Field(
        default=None, 
        description="Organization ID for Contexa Cloud deployments"
    )
    timeout: int = Field(
        default=60, 
        description="Timeout for API requests in seconds"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for tools and agents"
    )
    
    class Config:
        """Pydantic config for ContexaConfig.
        
        Configures the behavior of the Pydantic model, allowing for
        extra fields to be included beyond those explicitly defined.
        This makes the configuration future-proof as new features are added.
        """
        
        extra = "allow" 