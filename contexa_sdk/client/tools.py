"""Client module for accessing tools in Contexa."""

from typing import Dict, List, Any, Optional, Union

from contexa_sdk.core.config import ContexaConfig
from contexa_sdk.core.tool import RemoteTool
from contexa_sdk.client.registry import ResourceRegistry
from contexa_sdk.observability import get_logger, trace, SpanKind

# Create a logger for this module
logger = get_logger(__name__)


class ToolsWrapper:
    """Wrapper for a collection of tools, allowing framework conversion."""
    
    def __init__(
        self, 
        names: List[str], 
        config: Optional[ContexaConfig] = None,
        registry: Optional[ResourceRegistry] = None
    ):
        """Initialize the tools wrapper.
        
        Args:
            names: Names of the tools to access
            config: Configuration for API access
            registry: Resource registry (if None, a new one will be created)
        """
        from contexa_sdk.client import registry as default_registry
        self.names = names
        self.config = config or ContexaConfig()
        self.registry = registry or default_registry
        self._tools: Optional[List[Dict[str, Any]]] = None
        self._remote_tools: Optional[List[RemoteTool]] = None
    
    @trace(kind=SpanKind.INTERNAL)
    async def load(self) -> "ToolsWrapper":
        """Load the tools from the registry.
        
        Returns:
            Self, for method chaining
        """
        if self._tools is None:
            logger.info(f"Loading tools: {', '.join(self.names)}")
            try:
                self._tools = await self.registry.get_tools(self.names)
                self._remote_tools = [
                    RemoteTool(
                        name=tool["name"],
                        description=tool.get("description", ""),
                        endpoint=tool["endpoint"],
                        parameters=tool.get("parameters", {}),
                        config=self.config,
                    )
                    for tool in self._tools
                ]
                logger.info(f"Successfully loaded {len(self._tools)} tools")
            except Exception as e:
                logger.error(f"Error loading tools: {str(e)}")
                raise
        return self
    
    @trace(kind=SpanKind.INTERNAL)
    async def to_langchain(self) -> List[Any]:
        """Convert the tools to LangChain format.
        
        Returns:
            List of LangChain tools
        """
        # Ensure tools are loaded
        await self.load()
        
        # Import LangChain here to avoid dependency if not needed
        try:
            from langchain.tools import BaseTool as LangChainBaseTool
            from contexa_sdk.adapters.langchain import convert_tool_to_langchain
        except ImportError:
            logger.error("LangChain not installed. Please install langchain to use this feature.")
            raise ImportError("LangChain not installed. Please install langchain to use this feature.")
        
        # Convert each tool to LangChain format
        langchain_tools = []
        for tool in self._remote_tools:
            langchain_tool = await convert_tool_to_langchain(tool)
            langchain_tools.append(langchain_tool)
        
        return langchain_tools
    
    @trace(kind=SpanKind.INTERNAL)
    async def to_crewai(self) -> List[Any]:
        """Convert the tools to CrewAI format.
        
        Returns:
            List of CrewAI tools
        """
        # Ensure tools are loaded
        await self.load()
        
        # Import CrewAI here to avoid dependency if not needed
        try:
            from crewai.tools import BaseTool as CrewAIBaseTool
            from contexa_sdk.adapters.crewai import convert_tool_to_crewai
        except ImportError:
            logger.error("CrewAI not installed. Please install crewai to use this feature.")
            raise ImportError("CrewAI not installed. Please install crewai to use this feature.")
        
        # Convert each tool to CrewAI format
        crewai_tools = []
        for tool in self._remote_tools:
            crewai_tool = await convert_tool_to_crewai(tool)
            crewai_tools.append(crewai_tool)
        
        return crewai_tools
    
    @trace(kind=SpanKind.INTERNAL)
    async def to_native(self) -> List[RemoteTool]:
        """Get the tools as native Contexa RemoteTool objects.
        
        Returns:
            List of RemoteTool objects
        """
        # Ensure tools are loaded
        await self.load()
        return self._remote_tools


@trace(kind=SpanKind.INTERNAL)
async def ctx_tools(
    names: List[str],
    config: Optional[ContexaConfig] = None,
    registry: Optional[ResourceRegistry] = None
) -> ToolsWrapper:
    """Get tools by name.
    
    This is the main entry point for accessing tools.
    
    Args:
        names: Names of the tools to access
        config: Configuration for API access
        registry: Resource registry (if None, a global one will be used)
        
    Returns:
        A ToolsWrapper for the requested tools
    """
    wrapper = ToolsWrapper(names, config, registry)
    return wrapper 