"""Configuration for Contexa SDK."""

from typing import Dict, Optional, Any
from pydantic import BaseModel, Field


class ContexaConfig(BaseModel):
    """Configuration for Contexa SDK."""
    
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
        """Pydantic config for ContexaConfig."""
        
        extra = "allow" 