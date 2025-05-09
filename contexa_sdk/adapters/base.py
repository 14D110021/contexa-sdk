"""Base adapter interface for converting Contexa objects to framework-native objects."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.prompt import ContexaPrompt


class BaseAdapter(ABC):
    """Base adapter interface for converting Contexa objects to framework-native objects."""
    
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