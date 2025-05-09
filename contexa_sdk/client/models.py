"""Client module for accessing models in Contexa."""

from typing import Dict, List, Any, Optional, Union

from contexa_sdk.core.config import ContexaConfig
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.client.registry import ResourceRegistry
from contexa_sdk.observability import get_logger, trace, SpanKind

# Create a logger for this module
logger = get_logger(__name__)


class ModelWrapper:
    """Wrapper for a model, allowing framework conversion."""
    
    def __init__(
        self, 
        name: str, 
        config: Optional[ContexaConfig] = None,
        registry: Optional[ResourceRegistry] = None
    ):
        """Initialize the model wrapper.
        
        Args:
            name: Name of the model to access
            config: Configuration for API access
            registry: Resource registry (if None, a new one will be created)
        """
        from contexa_sdk.client import registry as default_registry
        self.name = name
        self.config = config or ContexaConfig()
        self.registry = registry or default_registry
        self._model_info: Optional[Dict[str, Any]] = None
        self._native_model: Optional[ContexaModel] = None
    
    @trace(kind=SpanKind.INTERNAL)
    async def load(self) -> "ModelWrapper":
        """Load the model from the registry.
        
        Returns:
            Self, for method chaining
        """
        if self._model_info is None:
            logger.info(f"Loading model: {self.name}")
            try:
                self._model_info = await self.registry.get_model(self.name)
                self._native_model = ContexaModel(
                    model_name=self._model_info["model_name"],
                    provider=self._model_info.get("provider", "contexa"),
                    config=self.config,
                )
                # Set additional model properties if present
                if "parameters" in self._model_info:
                    for k, v in self._model_info["parameters"].items():
                        setattr(self._native_model, k, v)
                        
                logger.info(f"Successfully loaded model {self.name}")
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
                raise
        return self
    
    @trace(kind=SpanKind.INTERNAL)
    async def to_langchain(self) -> Any:
        """Convert the model to LangChain format.
        
        Returns:
            LangChain model
        """
        # Ensure model is loaded
        await self.load()
        
        # Import LangChain here to avoid dependency if not needed
        try:
            from langchain.llms.base import BaseLLM
            from contexa_sdk.adapters.langchain import convert_model_to_langchain
        except ImportError:
            logger.error("LangChain not installed. Please install langchain to use this feature.")
            raise ImportError("LangChain not installed. Please install langchain to use this feature.")
        
        # Convert to LangChain format
        langchain_model = await convert_model_to_langchain(self._native_model)
        return langchain_model
    
    @trace(kind=SpanKind.INTERNAL)
    async def to_crewai(self) -> Any:
        """Convert the model to CrewAI format.
        
        Returns:
            CrewAI model
        """
        # Ensure model is loaded
        await self.load()
        
        # Import CrewAI here to avoid dependency if not needed
        try:
            from contexa_sdk.adapters.crewai import convert_model_to_crewai
        except ImportError:
            logger.error("CrewAI not installed. Please install crewai to use this feature.")
            raise ImportError("CrewAI not installed. Please install crewai to use this feature.")
        
        # Convert to CrewAI format
        crewai_model = await convert_model_to_crewai(self._native_model)
        return crewai_model
    
    @trace(kind=SpanKind.INTERNAL)
    async def to_native(self) -> ContexaModel:
        """Get the model as a native Contexa ContexaModel object.
        
        Returns:
            ContexaModel object
        """
        # Ensure model is loaded
        await self.load()
        return self._native_model


@trace(kind=SpanKind.INTERNAL)
async def ctx_model(
    name: str,
    config: Optional[ContexaConfig] = None,
    registry: Optional[ResourceRegistry] = None
) -> ModelWrapper:
    """Get a model by name.
    
    This is the main entry point for accessing models.
    
    Args:
        name: Name of the model to access
        config: Configuration for API access
        registry: Resource registry (if None, a global one will be used)
        
    Returns:
        A ModelWrapper for the requested model
    """
    wrapper = ModelWrapper(name, config, registry)
    return wrapper 