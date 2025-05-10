"""Tests for compatibility with various frameworks."""

import unittest
import os
import asyncio
from typing import Any, Dict, List, Optional, Union
from unittest.mock import patch, MagicMock

from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel


class TestLangChainCompatibility(unittest.TestCase):
    """Test compatibility with LangChain."""

    @patch("langchain_core.tools.BaseTool")
    @patch("langchain_core.tools.StructuredTool")
    @patch("langchain_core.pydantic_v1.BaseModel")
    @patch("langchain_core.pydantic_v1.create_model")
    def test_tool_conversion(self, mock_create_model, mock_base_model, mock_structured_tool, mock_base_tool):
        """Test converting a Contexa tool to a LangChain tool."""
        # Skip if langchain is not installed
        try:
            from contexa_sdk.adapters import langchain
        except ImportError:
            self.skipTest("LangChain not installed")
            
        # Create a mock Contexa tool
        tool = MagicMock(spec=ContexaTool)
        tool.name = "test_tool"
        tool.description = "Test tool"
        tool.schema.model_json_schema.return_value = {"properties": {}}
        
        # Convert the tool to LangChain
        lc_tool = langchain.tool(tool)
        
        # Assert import attempt was made
        self.assertTrue(mock_base_tool.called or mock_structured_tool.called)
        self.assertTrue(mock_create_model.called)


class TestOpenAIAgentsCompatibility(unittest.TestCase):
    """Test compatibility with OpenAI Agents SDK."""

    @patch("agents.function_tool")
    def test_tool_conversion(self, mock_function_tool):
        """Test converting a Contexa tool to an OpenAI Agents SDK tool."""
        # Skip if OpenAI Agents SDK is not installed
        try:
            from contexa_sdk.adapters import openai
        except ImportError:
            self.skipTest("OpenAI Agents SDK not installed")
            
        # Create a mock Contexa tool
        tool = MagicMock(spec=ContexaTool)
        tool.name = "test_tool"
        tool.description = "Test tool"
        
        # Mock the decorator to return the function
        mock_function_tool.return_value = lambda x: x
        
        # Convert the tool to OpenAI Agents SDK
        openai_tool = openai.tool(tool)
        
        # Assert import attempt was made
        self.assertTrue(mock_function_tool.called)


class TestCrewAICompatibility(unittest.TestCase):
    """Test compatibility with CrewAI."""

    @patch("crewai.tools.tool")
    def test_tool_conversion(self, mock_tool_decorator):
        """Test converting a Contexa tool to a CrewAI tool."""
        # Skip if CrewAI is not installed
        try:
            from contexa_sdk.adapters import crewai
        except ImportError:
            self.skipTest("CrewAI not installed")
            
        # Create a mock Contexa tool
        tool = MagicMock(spec=ContexaTool)
        tool.name = "test_tool"
        tool.description = "Test tool"
        
        # Mock the decorator to return the function
        mock_tool_decorator.return_value = lambda x: x
        
        # Convert the tool to CrewAI
        crew_tool = crewai.tool(tool)
        
        # Assert import attempt was made
        self.assertTrue(mock_tool_decorator.called)


class TestGoogleAICompatibility(unittest.TestCase):
    """Test compatibility with Google GenAI SDK."""

    @patch("google.genai.types")
    def test_tool_conversion(self, mock_types):
        """Test converting a Contexa tool to a Google GenAI tool."""
        # Skip if Google GenAI SDK is not installed
        try:
            from contexa_sdk.adapters import google_adk
        except ImportError:
            self.skipTest("Google GenAI SDK not installed")
            
        # Create a mock Contexa tool
        tool = MagicMock(spec=ContexaTool)
        tool.name = "test_tool"
        tool.description = "Test tool"
        
        # Convert the tool to Google GenAI
        google_tool = google_adk.tool(tool)
        
        # Assert tool was converted
        self.assertEqual(google_tool.__name__, "test_tool")
        self.assertEqual(google_tool.__doc__, "Test tool")


if __name__ == "__main__":
    unittest.main() 