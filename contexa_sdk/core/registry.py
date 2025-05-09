"""Registry module for Contexa SDK."""

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
    
    Args:
        tool: The tool to register
    """
    _tools[tool.tool_id] = tool
    

def register_agent(agent: ContexaAgent) -> None:
    """Register an agent in the global registry.
    
    Args:
        agent: The agent to register
    """
    _agents[agent.agent_id] = agent
    

def register_model(model: ContexaModel, model_id: str) -> None:
    """Register a model in the global registry.
    
    Args:
        model: The model to register
        model_id: ID for the model
    """
    _models[model_id] = model
    

def register_prompt(prompt: ContexaPrompt) -> None:
    """Register a prompt in the global registry.
    
    Args:
        prompt: The prompt to register
    """
    _prompts[prompt.prompt_id] = prompt
    

def get_tool(tool_id: str) -> Optional[ContexaTool]:
    """Get a tool from the global registry.
    
    Args:
        tool_id: ID of the tool to get
        
    Returns:
        The tool, or None if not found
    """
    return _tools.get(tool_id)
    

def get_agent(agent_id: str) -> Optional[ContexaAgent]:
    """Get an agent from the global registry.
    
    Args:
        agent_id: ID of the agent to get
        
    Returns:
        The agent, or None if not found
    """
    return _agents.get(agent_id)
    

def get_model(model_id: str) -> Optional[ContexaModel]:
    """Get a model from the global registry.
    
    Args:
        model_id: ID of the model to get
        
    Returns:
        The model, or None if not found
    """
    return _models.get(model_id)
    

def get_prompt(prompt_id: str) -> Optional[ContexaPrompt]:
    """Get a prompt from the global registry.
    
    Args:
        prompt_id: ID of the prompt to get
        
    Returns:
        The prompt, or None if not found
    """
    return _prompts.get(prompt_id)
    

def list_tools() -> List[ContexaTool]:
    """List all tools in the global registry.
    
    Returns:
        List of all tools
    """
    return list(_tools.values())
    

def list_agents() -> List[ContexaAgent]:
    """List all agents in the global registry.
    
    Returns:
        List of all agents
    """
    return list(_agents.values())
    

def list_models() -> List[ContexaModel]:
    """List all models in the global registry.
    
    Returns:
        List of all models
    """
    return list(_models.values())
    

def list_prompts() -> List[ContexaPrompt]:
    """List all prompts in the global registry.
    
    Returns:
        List of all prompts
    """
    return list(_prompts.values())
    

def clear_registry() -> None:
    """Clear all registries."""
    _tools.clear()
    _agents.clear()
    _models.clear()
    _prompts.clear() 