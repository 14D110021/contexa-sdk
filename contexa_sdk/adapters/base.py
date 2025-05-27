"""Base adapter interface for converting Contexa objects to framework-native objects.

This module defines the abstract base class for all framework adapters in the Contexa SDK.
Framework adapters are responsible for converting Contexa SDK core objects (tools, models,
agents, and prompts) into their framework-specific equivalents.

The adapter system allows Contexa SDK components to be used with multiple different
agent frameworks while maintaining a consistent interface. Each adapter implements
the methods defined in the BaseAdapter abstract class.

Typical usage:
    # Create a framework-specific adapter
    from contexa_sdk.adapters import langchain
    
    # Convert Contexa objects to framework objects
    langchain_tool = langchain.tool(my_contexa_tool)
    langchain_agent = langchain.agent(my_contexa_agent)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.prompt import ContexaPrompt

# Adapter version
__adapter_version__ = "0.1.0"


class BaseAdapter(ABC):
    """Base adapter interface for converting Contexa objects to framework-native objects.
    
    This abstract base class defines the standard interface that all framework adapters
    must implement. Each adapter provides methods to convert core Contexa objects
    (tools, models, agents, and prompts) to their framework-specific equivalents.
    
    Framework-specific adapters should inherit from this class and implement the
    required abstract methods. The adapter system enables cross-framework compatibility
    and standardized conversion between different agent frameworks.
    
    Attributes:
        None
        
    Methods:
        tool: Convert a Contexa tool to a framework-native tool
        model: Convert a Contexa model to a framework-native model
        agent: Convert a Contexa agent to a framework-native agent
        prompt: Convert a Contexa prompt to a framework-native prompt
    """
    
    @abstractmethod
    def tool(self, tool: ContexaTool) -> Any:
        """Convert a Contexa tool to a framework-native tool.
        
        Args:
            tool: The Contexa tool to convert
            
        Returns:
            A framework-native tool object
        """
        pass
        
    @abstractmethod
    def model(self, model: ContexaModel) -> Any:
        """Convert a Contexa model to a framework-native model.
        
        Args:
            model: The Contexa model to convert
            
        Returns:
            A framework-native model object
        """
        pass
        
    @abstractmethod
    def agent(self, agent: ContexaAgent) -> Any:
        """Convert a Contexa agent to a framework-native agent.
        
        Args:
            agent: The Contexa agent to convert
            
        Returns:
            A framework-native agent object
        """
        pass
        
    def prompt(self, prompt: ContexaPrompt) -> Any:
        """Convert a Contexa prompt to a framework-native prompt.
        
        Args:
            prompt: The Contexa prompt to convert
            
        Returns:
            A framework-native prompt object
        """
        # Default implementation just returns the template string
        return prompt.template 