"""Tests for Google GenAI adapter-specific features."""

import unittest
from unittest.mock import patch, MagicMock
import asyncio
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool
from pydantic import BaseModel


class TestGoogleGenAIFeatures(unittest.TestCase):
    """Test Google GenAI adapter-specific features."""

    def setUp(self):
        """Set up the test environment."""
        # Define a test tool
        class SearchInput(BaseModel):
            query: str

        @ContexaTool.register(
            name="search", 
            description="Search for information"
        )
        async def search_tool(inp: SearchInput) -> str:
            return f"Results for {inp.query}"

        self.tool = search_tool
        self.model = ContexaModel(
            provider="google", 
            model_name="gemini-pro",
            temperature=0.7
        )

    @patch("google.generativeai", autospec=True)
    def test_genai_streaming_support(self, mock_genai):
        """Test that GenAI adapter supports streaming responses."""
        from contexa_sdk.adapters.google import genai_model
        
        # Set up mock stream behavior
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Create mock streaming response
        mock_stream = MagicMock()
        mock_stream.text = "Streaming response"
        mock_stream.__aiter__ = MagicMock()
        mock_stream.__aiter__.return_value = [mock_stream]
        
        # Configure model generate_content to return stream
        mock_model.generate_content.return_value = mock_stream
        
        # Convert model
        google_model = genai_model(self.model)
        
        # Test streaming capability
        result = asyncio.run(google_model.generate_stream("Test prompt"))
        self.assertIsNotNone(result)
        
        # Verify streaming was used
        mock_model.generate_content.assert_called_once()
        call_kwargs = mock_model.generate_content.call_args[1]
        self.assertTrue(call_kwargs.get("stream", False))

    @patch("google.generativeai", autospec=True)
    def test_genai_function_calling(self, mock_genai):
        """Test that GenAI adapter supports function calling."""
        from contexa_sdk.adapters.google import genai_tool, genai_model
        
        # Set up mock behavior for function calling
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Create mock response that includes function call
        mock_response = MagicMock()
        mock_candidates = [MagicMock()]
        mock_content = MagicMock()
        mock_parts = [MagicMock()]
        
        mock_function_call = MagicMock()
        mock_function_call.name = "search"
        mock_function_call.args = {"query": "test query"}
        
        mock_parts[0].function_call = mock_function_call
        mock_content.parts = mock_parts
        mock_candidates[0].content = mock_content
        mock_response.candidates = mock_candidates
        
        mock_model.generate_content.return_value = mock_response
        
        # Convert tool and model
        google_tool = genai_tool(self.tool)
        google_model = genai_model(self.model)
        
        # Test function calling
        tools = [google_tool]
        result = asyncio.run(google_model.generate_with_tools("Use the search tool", tools))
        
        # Verify function calling setup
        mock_model.generate_content.assert_called_once()
        call_args, call_kwargs = mock_model.generate_content.call_args
        
        # Verify tools were passed to the model
        self.assertIn("tools", call_kwargs)
        
    @patch("google.generativeai", autospec=True)
    def test_genai_safety_settings(self, mock_genai):
        """Test that GenAI adapter supports safety settings."""
        from contexa_sdk.adapters.google import genai_model
        
        # Create mock safety settings
        mock_safety = MagicMock()
        mock_genai.types.SafetySettings = mock_safety
        
        # Create model with safety settings
        model_with_safety = ContexaModel(
            provider="google", 
            model_name="gemini-pro",
            safety_settings={
                "harassment": "block_none",
                "hate_speech": "block_medium_and_above"
            }
        )
        
        # Convert model
        google_model = genai_model(model_with_safety)
        
        # Verify safety settings were configured
        mock_genai.GenerativeModel.assert_called_once()
        call_kwargs = mock_genai.GenerativeModel.call_args[1]
        self.assertIn("safety_settings", call_kwargs)
    
    @patch("google.generativeai", autospec=True)
    def test_genai_system_instructions(self, mock_genai):
        """Test that GenAI adapter supports system instructions."""
        from contexa_sdk.adapters.google import genai_model
        
        # Create model with system instruction
        model_with_system = ContexaModel(
            provider="google", 
            model_name="gemini-pro",
            system_prompt="You are a helpful assistant"
        )
        
        # Convert model
        google_model = genai_model(model_with_system)
        
        # Verify system instruction was configured
        mock_genai.GenerativeModel.assert_called_once()
        call_kwargs = mock_genai.GenerativeModel.call_args[1]
        self.assertIn("system_instruction", call_kwargs)
        
    @patch("google.generativeai", autospec=True)
    def test_genai_with_decorator_pattern(self, mock_genai):
        """Test that GenAI adapter works with decorator pattern."""
        from contexa_sdk.adapters.google import genai_tool
        
        # Define a tool with decorator pattern
        @ContexaTool.register(
            name="calculator", 
            description="Perform calculation"
        )
        async def calculator(expression: str) -> float:
            return eval(expression)
        
        # Convert tool using decorator pattern
        google_tool = genai_tool(calculator)
        
        # Verify the tool was converted correctly
        self.assertEqual(google_tool.__name__, "calculator")
        
    @patch("google.generativeai", autospec=True)
    def test_genai_with_direct_tool_instance(self, mock_genai):
        """Test that GenAI adapter works with direct tool instance."""
        from contexa_sdk.adapters.google import genai_tool
        
        # Create a direct tool instance
        tool = ContexaTool(
            name="weather",
            description="Get weather information",
            function=lambda location: f"Weather in {location} is sunny"
        )
        
        # Convert tool using direct instance
        google_tool = genai_tool(tool)
        
        # Verify the tool was converted correctly
        self.assertEqual(google_tool.__name__, "weather")


if __name__ == "__main__":
    unittest.main() 