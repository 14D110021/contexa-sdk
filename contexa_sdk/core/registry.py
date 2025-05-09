"""Registry module for Contexa SDK.

This module provides a centralized registry system for managing Contexa objects
including tools, agents, models, and prompts. The registry allows for easy access
to these objects across different parts of an application without having to pass
them around explicitly.

The registry maintains separate collections for each type of object, indexed by
their unique IDs. Objects can be registered, retrieved, listed, and the entire
registry can be cleared when needed.

Examples:
    Register and retrieve a tool:
    
    ```python
    from contexa_sdk.core.registry import register_tool, get_tool
    from contexa_sdk.core.tool import ContexaTool
    
    # Create and register a tool
    search_tool = ContexaTool(...)
    register_tool(search_tool)
    
    # Later, retrieve the tool by its ID
    tool = get_tool(search_tool.tool_id)
    ```
    
    List all registered objects of a certain type:
    
    ```python
    from contexa_sdk.core.registry import list_tools, list_agents
    
    # Get all registered tools
    all_tools = list_tools()
    
    # Get all registered agents
    all_agents = list_agents()
    ```
"""

from typing import Dict, List, Optional

from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.prompt import ContexaPrompt


# Global registries
_tools: Dict[str, ContexaTool] = {}
_agents: Dict[str, ContexaAgent] = {}
_models: Dict[str, ContexaModel] = {}
_prompts: Dict[str, ContexaPrompt] = {}


def register_tool(tool: ContexaTool) -> None:
    """Register a tool in the global registry.
    
    Adds a tool to the global tool registry, indexed by its tool_id.
    If a tool with the same ID already exists, it will be overwritten.
    
    Args:
        tool (ContexaTool): The tool to register
    """
    _tools[tool.tool_id] = tool
    

def register_agent(agent: ContexaAgent) -> None:
    """Register an agent in the global registry.
    
    Adds an agent to the global agent registry, indexed by its agent_id.
    If an agent with the same ID already exists, it will be overwritten.
    
    Args:
        agent (ContexaAgent): The agent to register
    """
    _agents[agent.agent_id] = agent
    

def register_model(model: ContexaModel, model_id: str) -> None:
    """Register a model in the global registry.
    
    Adds a model to the global model registry, indexed by the provided model_id.
    If a model with the same ID already exists, it will be overwritten.
    
    Args:
        model (ContexaModel): The model to register
        model_id (str): ID for the model to use as index in the registry
    """
    _models[model_id] = model
    

def register_prompt(prompt: ContexaPrompt) -> None:
    """Register a prompt in the global registry.
    
    Adds a prompt to the global prompt registry, indexed by its prompt_id.
    If a prompt with the same ID already exists, it will be overwritten.
    
    Args:
        prompt (ContexaPrompt): The prompt to register
    """
    _prompts[prompt.prompt_id] = prompt
    

def get_tool(tool_id: str) -> Optional[ContexaTool]:
    """Get a tool from the global registry.
    
    Retrieves a tool from the global registry by its ID.
    
    Args:
        tool_id (str): ID of the tool to get
        
    Returns:
        Optional[ContexaTool]: The tool if found, or None if not found
    """
    return _tools.get(tool_id)
    

def get_agent(agent_id: str) -> Optional[ContexaAgent]:
    """Get an agent from the global registry.
    
    Retrieves an agent from the global registry by its ID.
    
    Args:
        agent_id (str): ID of the agent to get
        
    Returns:
        Optional[ContexaAgent]: The agent if found, or None if not found
    """
    return _agents.get(agent_id)
    

def get_model(model_id: str) -> Optional[ContexaModel]:
    """Get a model from the global registry.
    
    Retrieves a model from the global registry by its ID.
    
    Args:
        model_id (str): ID of the model to get
        
    Returns:
        Optional[ContexaModel]: The model if found, or None if not found
    """
    return _models.get(model_id)
    

def get_prompt(prompt_id: str) -> Optional[ContexaPrompt]:
    """Get a prompt from the global registry.
    
    Retrieves a prompt from the global registry by its ID.
    
    Args:
        prompt_id (str): ID of the prompt to get
        
    Returns:
        Optional[ContexaPrompt]: The prompt if found, or None if not found
    """
    return _prompts.get(prompt_id)
    

def list_tools() -> List[ContexaTool]:
    """List all tools in the global registry.
    
    Returns a list of all tools currently registered in the global registry.
    The order of tools in the list is not guaranteed to be consistent.
    
    Returns:
        List[ContexaTool]: List of all registered tools
    """
    return list(_tools.values())
    

def list_agents() -> List[ContexaAgent]:
    """List all agents in the global registry.
    
    Returns a list of all agents currently registered in the global registry.
    The order of agents in the list is not guaranteed to be consistent.
    
    Returns:
        List[ContexaAgent]: List of all registered agents
    """
    return list(_agents.values())
    

def list_models() -> List[ContexaModel]:
    """List all models in the global registry.
    
    Returns a list of all models currently registered in the global registry.
    The order of models in the list is not guaranteed to be consistent.
    
    Returns:
        List[ContexaModel]: List of all registered models
    """
    return list(_models.values())
    

def list_prompts() -> List[ContexaPrompt]:
    """List all prompts in the global registry.
    
    Returns a list of all prompts currently registered in the global registry.
    The order of prompts in the list is not guaranteed to be consistent.
    
    Returns:
        List[ContexaPrompt]: List of all registered prompts
    """
    return list(_prompts.values())
    

def clear_registry() -> None:
    """Clear all registries.
    
    Removes all tools, agents, models, and prompts from their respective
    global registries. This is useful for unit tests, or when resetting
    an application's state.
    """
    _tools.clear()
    _agents.clear()
    _models.clear()
    _prompts.clear() 