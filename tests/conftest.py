"""
Pytest configuration for Contexa SDK tests.
This file contains fixtures and configuration for testing the Contexa SDK.
"""

import os
import sys
import pytest
import asyncio
from typing import Dict, Any, List, Optional

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock framework imports for testing without dependencies
class MockImport:
    """Mock import handler for testing without actual dependencies."""
    
    def __init__(self, modules=None):
        self.modules = modules or {}
        
    def __call__(self, name, *args, **kwargs):
        if name in self.modules:
            return self.modules[name]
        raise ImportError(f"No module named '{name}'")


@pytest.fixture
def mock_openai():
    """Mock OpenAI module for testing."""
    class MockOpenAI:
        """Mock OpenAI client."""
        def __init__(self, api_key=None):
            self.api_key = api_key or "test_api_key"
            
    class MockOpenAIAgents:
        """Mock OpenAI Agents SDK."""
        class Agent:
            def __init__(self, name, tools=None, **kwargs):
                self.name = name
                self.tools = tools or []
                self.kwargs = kwargs
                
        class Tool:
            def __init__(self, name, description=None, function=None, **kwargs):
                self.name = name
                self.description = description
                self.function = function
                self.kwargs = kwargs
    
    return {
        "openai": MockOpenAI,
        "openai_agents": MockOpenAIAgents
    }


@pytest.fixture
def mock_langchain():
    """Mock LangChain modules for testing."""
    class MockLangChain:
        """Mock LangChain classes and utilities."""
        class BaseChatModel:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                
        class AgentExecutor:
            def __init__(self, agent, tools, **kwargs):
                self.agent = agent
                self.tools = tools
                self.kwargs = kwargs
                
        class Tool:
            def __init__(self, name, func, description, **kwargs):
                self.name = name
                self.func = func
                self.description = description
                self.kwargs = kwargs
    
    return {
        "langchain_core.language_models.chat_models": type('obj', (object,), {
            'BaseChatModel': MockLangChain.BaseChatModel
        }),
        "langchain.agents": type('obj', (object,), {
            'AgentExecutor': MockLangChain.AgentExecutor
        }),
        "langchain_core.tools": type('obj', (object,), {
            'Tool': MockLangChain.Tool
        })
    }


@pytest.fixture
def mock_crewai():
    """Mock CrewAI module for testing."""
    class MockCrewAI:
        """Mock CrewAI classes."""
        class Agent:
            def __init__(self, role, goal, backstory=None, tools=None, **kwargs):
                self.role = role
                self.goal = goal
                self.backstory = backstory
                self.tools = tools or []
                self.kwargs = kwargs
                
        class Crew:
            def __init__(self, agents, tasks=None, **kwargs):
                self.agents = agents
                self.tasks = tasks or []
                self.kwargs = kwargs
                
        class Tool:
            def __init__(self, name, description=None, func=None, **kwargs):
                self.name = name
                self.description = description
                self.func = func
                self.kwargs = kwargs
    
    return {
        "crewai": type('obj', (object,), {
            'Agent': MockCrewAI.Agent,
            'Crew': MockCrewAI.Crew,
            'Tool': MockCrewAI.Tool
        })
    }


@pytest.fixture
def mock_google_adk():
    """Mock Google ADK module for testing."""
    class MockGoogleADK:
        """Mock Google ADK classes."""
        class Agent:
            def __init__(self, model, tools=None, **kwargs):
                self.model = model
                self.tools = tools or []
                self.kwargs = kwargs
                
        class Tool:
            def __init__(self, name, description=None, function=None, **kwargs):
                self.name = name
                self.description = description
                self.function = function
                self.kwargs = kwargs
                
        class genai:
            def configure(self, api_key=None):
                self.api_key = api_key
    
    return {
        "google.adk": type('obj', (object,), {
            'Agent': MockGoogleADK.Agent,
            'Tool': MockGoogleADK.Tool
        }),
        "google.genai": type('obj', (object,), {
            'configure': MockGoogleADK.genai().configure
        })
    }


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 