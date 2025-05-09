"""Resource registry for Contexa SDK."""

import os
import json
import httpx
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic, Type

from contexa_sdk.core.config import ContexaConfig
from contexa_sdk.observability import get_logger

# Create a logger for this module
logger = get_logger(__name__)

# Type variable for resource types
T = TypeVar('T')


class ResourceRegistry(Generic[T]):
    """Registry for Contexa resources (agents, models, tools, etc).
    
    This registry allows looking up resources by name and provides
    caching to avoid repeated API calls.
    """
    
    def __init__(self, config: Optional[ContexaConfig] = None):
        """Initialize the resource registry.
        
        Args:
            config: Configuration for API access
        """
        self.config = config or ContexaConfig()
        self._cache: Dict[str, Dict[str, Any]] = {
            "agents": {},
            "models": {},
            "tools": {},
        }
        self._resource_loaded: Dict[str, bool] = {
            "agents": False,
            "models": False,
            "tools": False,
        }
    
    async def get_agent(self, name: str) -> Dict[str, Any]:
        """Get an agent by name.
        
        Args:
            name: Name of the agent
            
        Returns:
            Agent details
            
        Raises:
            ValueError: If the agent is not found
        """
        return await self._get_resource("agents", name)
    
    async def get_model(self, name: str) -> Dict[str, Any]:
        """Get a model by name.
        
        Args:
            name: Name of the model
            
        Returns:
            Model details
            
        Raises:
            ValueError: If the model is not found
        """
        return await self._get_resource("models", name)
    
    async def get_tools(self, names: List[str]) -> List[Dict[str, Any]]:
        """Get tools by name.
        
        Args:
            names: Names of the tools
            
        Returns:
            List of tool details
            
        Raises:
            ValueError: If any tool is not found
        """
        result = []
        for name in names:
            tool = await self._get_resource("tools", name)
            result.append(tool)
        return result
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all available agents.
        
        Returns:
            List of agent details
        """
        await self._ensure_resources_loaded("agents")
        return list(self._cache["agents"].values())
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List all available models.
        
        Returns:
            List of model details
        """
        await self._ensure_resources_loaded("models")
        return list(self._cache["models"].values())
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools.
        
        Returns:
            List of tool details
        """
        await self._ensure_resources_loaded("tools")
        return list(self._cache["tools"].values())
    
    async def _get_resource(self, resource_type: str, name: str) -> Dict[str, Any]:
        """Get a resource by type and name.
        
        Args:
            resource_type: Type of resource
            name: Name of the resource
            
        Returns:
            Resource details
            
        Raises:
            ValueError: If the resource is not found
        """
        # Ensure resources are loaded
        await self._ensure_resources_loaded(resource_type)
        
        # Check if the resource is in the cache
        if name in self._cache[resource_type]:
            return self._cache[resource_type][name]
        
        # If not, try to fetch it specifically
        try:
            resource = await self._fetch_resource(resource_type, name)
            self._cache[resource_type][name] = resource
            return resource
        except Exception as e:
            logger.error(f"Error fetching {resource_type} '{name}': {str(e)}")
            raise ValueError(f"{resource_type.title()} '{name}' not found") from e
    
    async def _fetch_resources(self, resource_type: str) -> Dict[str, Dict[str, Any]]:
        """Fetch all resources of a given type.
        
        Args:
            resource_type: Type of resource
            
        Returns:
            Dictionary of resources, keyed by name
        """
        # In a real implementation, this would make an HTTP request
        # to the Contexa API to fetch all resources of the given type.
        # For now, we'll check for local .ctx or environment resources
        
        # First try loading from .ctx directory
        ctx_dir = os.path.join(os.getcwd(), ".ctx", resource_type)
        if os.path.exists(ctx_dir):
            resources = {}
            for filename in os.listdir(ctx_dir):
                if filename.endswith(".json"):
                    with open(os.path.join(ctx_dir, filename), "r") as f:
                        resource = json.load(f)
                        if "name" in resource:
                            resources[resource["name"]] = resource
            return resources
        
        # Try loading from API
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                headers = {"Content-Type": "application/json"}
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"
                
                response = await client.get(
                    f"{self.config.api_url}/{resource_type}",
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                
                # Convert to dictionary keyed by name
                resources = {}
                for resource in data:
                    if "name" in resource:
                        resources[resource["name"]] = resource
                return resources
        except Exception as e:
            logger.warning(f"Error fetching {resource_type} from API: {str(e)}")
            # For now, just return an empty dictionary
            return {}
    
    async def _fetch_resource(self, resource_type: str, name: str) -> Dict[str, Any]:
        """Fetch a specific resource.
        
        Args:
            resource_type: Type of resource
            name: Name of the resource
            
        Returns:
            Resource details
            
        Raises:
            Exception: If the resource is not found or an error occurs
        """
        # Try loading from API
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                headers = {"Content-Type": "application/json"}
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"
                
                response = await client.get(
                    f"{self.config.api_url}/{resource_type}/{name}",
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching {resource_type} '{name}' from API: {str(e)}")
            raise
    
    async def _ensure_resources_loaded(self, resource_type: str) -> None:
        """Ensure resources of the given type are loaded.
        
        Args:
            resource_type: Type of resource
        """
        if not self._resource_loaded[resource_type]:
            resources = await self._fetch_resources(resource_type)
            self._cache[resource_type].update(resources)
            self._resource_loaded[resource_type] = True 