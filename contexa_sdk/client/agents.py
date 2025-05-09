"""Client module for accessing agents in Contexa."""

from typing import Dict, List, Any, Optional, Union

from contexa_sdk.core.config import ContexaConfig
from contexa_sdk.core.agent import RemoteAgent
from contexa_sdk.client.registry import ResourceRegistry
from contexa_sdk.observability import get_logger, trace, SpanKind

# Create a logger for this module
logger = get_logger(__name__)


class AgentWrapper:
    """Wrapper for an agent, allowing direct execution and framework conversion."""
    
    def __init__(
        self, 
        name: str, 
        config: Optional[ContexaConfig] = None,
        registry: Optional[ResourceRegistry] = None
    ):
        """Initialize the agent wrapper.
        
        Args:
            name: Name of the agent to access
            config: Configuration for API access
            registry: Resource registry (if None, a new one will be created)
        """
        from contexa_sdk.client import registry as default_registry
        self.name = name
        self.config = config or ContexaConfig()
        self.registry = registry or default_registry
        self._agent_info: Optional[Dict[str, Any]] = None
        self._remote_agent: Optional[RemoteAgent] = None
    
    @trace(kind=SpanKind.INTERNAL)
    async def load(self) -> "AgentWrapper":
        """Load the agent from the registry.
        
        Returns:
            Self, for method chaining
        """
        if self._agent_info is None:
            logger.info(f"Loading agent: {self.name}")
            try:
                self._agent_info = await self.registry.get_agent(self.name)
                endpoint_url = self._agent_info.get("endpoint_url")
                if not endpoint_url:
                    raise ValueError(f"Agent {self.name} does not have an endpoint URL")
                
                # Create a RemoteAgent for the endpoint
                self._remote_agent = await RemoteAgent.from_endpoint(
                    endpoint_url=endpoint_url,
                    config=self.config,
                )
                
                logger.info(f"Successfully loaded agent {self.name}")
            except Exception as e:
                logger.error(f"Error loading agent: {str(e)}")
                raise
        return self
    
    @trace(kind=SpanKind.AGENT)
    async def run(self, query: str, **kwargs) -> str:
        """Run the agent with a query.
        
        Args:
            query: The query to send to the agent
            **kwargs: Additional parameters to pass to the agent
            
        Returns:
            Agent response
        """
        # Ensure agent is loaded
        await self.load()
        
        logger.info(f"Running agent {self.name} with query: {query}")
        
        # Run the agent
        try:
            response = await self._remote_agent.run(query, **kwargs)
            return response
        except Exception as e:
            logger.error(f"Error running agent {self.name}: {str(e)}")
            raise
    
    @trace(kind=SpanKind.INTERNAL)
    async def to_langchain(self) -> Any:
        """Convert the agent to LangChain format.
        
        Returns:
            LangChain agent
        """
        # Ensure agent is loaded
        await self.load()
        
        # Import LangChain here to avoid dependency if not needed
        try:
            from contexa_sdk.adapters.langchain import convert_agent_to_langchain
        except ImportError:
            logger.error("LangChain not installed. Please install langchain to use this feature.")
            raise ImportError("LangChain not installed. Please install langchain to use this feature.")
        
        # Convert to LangChain format
        langchain_agent = await convert_agent_to_langchain(self._remote_agent)
        return langchain_agent
    
    @trace(kind=SpanKind.INTERNAL)
    async def to_crewai(self) -> Any:
        """Convert the agent to CrewAI format.
        
        Returns:
            CrewAI agent
        """
        # Ensure agent is loaded
        await self.load()
        
        # Import CrewAI here to avoid dependency if not needed
        try:
            from contexa_sdk.adapters.crewai import convert_agent_to_crewai
        except ImportError:
            logger.error("CrewAI not installed. Please install crewai to use this feature.")
            raise ImportError("CrewAI not installed. Please install crewai to use this feature.")
        
        # Convert to CrewAI format
        crewai_agent = await convert_agent_to_crewai(self._remote_agent)
        return crewai_agent
    
    @trace(kind=SpanKind.INTERNAL)
    async def to_native(self) -> RemoteAgent:
        """Get the agent as a native Contexa RemoteAgent object.
        
        Returns:
            RemoteAgent object
        """
        # Ensure agent is loaded
        await self.load()
        return self._remote_agent


@trace(kind=SpanKind.INTERNAL)
async def ctx_agent(
    name: str,
    config: Optional[ContexaConfig] = None,
    registry: Optional[ResourceRegistry] = None
) -> AgentWrapper:
    """Get an agent by name.
    
    This is the main entry point for accessing agents.
    
    Args:
        name: Name of the agent to access
        config: Configuration for API access
        registry: Resource registry (if None, a global one will be used)
        
    Returns:
        An AgentWrapper for the requested agent
    """
    wrapper = AgentWrapper(name, config, registry)
    return wrapper 