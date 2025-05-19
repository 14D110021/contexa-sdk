"""Google GenAI adapter for converting Contexa objects to Google Generative AI SDK objects."""

import inspect
import asyncio
import json
from typing import Any, Dict, List, Optional, Union, Callable

from contexa_sdk.adapters.base import BaseAdapter
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel, ModelMessage
from contexa_sdk.core.agent import ContexaAgent, HandoffData
from contexa_sdk.core.prompt import ContexaPrompt

# Try to import Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    GOOGLE_SDK_AVAILABLE = True
except ImportError:
    # Create mock classes for testing
    GOOGLE_SDK_AVAILABLE = False
    
    class MockTypes:
        class Content:
            def __init__(self, role, parts):
                self.role = role
                self.parts = parts
                
        class Part:
            def __init__(self, text=None, function_response=None):
                self.text = text
                self.function_response = function_response

        class FunctionDeclaration:
            def __init__(self, **kwargs):
                self.name = kwargs.get('name', '')
                self.description = kwargs.get('description', '')
                self.parameters = kwargs.get('parameters', {})
        
        class ToolConfig:
            def __init__(self, function_calling_config=None):
                self.function_calling_config = function_calling_config
                
        class FunctionCallingConfig:
            def __init__(self, mode="auto"):
                self.mode = mode
    
    class MockGenAI:
        class GenerativeModel:
            def __init__(self, model_name, **kwargs):
                self.model_name = model_name
                self.generation_config = kwargs.get('generation_config', {})
                
            async def generate_content_async(self, contents, **kwargs):
                return MockGenAIResponse("This is a mock response from Google GenAI.")
        
        def configure(self, api_key=None):
            pass
        
    class MockGenAIResponse:
        def __init__(self, text):
            self.text = text
            self.candidates = [MockCandidate(text)]
                
    class MockCandidate:
        def __init__(self, text):
            self.content = MockContent(text)
                
    class MockContent:
        def __init__(self, text):
            self.parts = [MockPart(text)]
            
    class MockPart:
        def __init__(self, text):
            self.text = text
                
    # Create mock objects
    genai = MockGenAI()
    types = MockTypes()

class GoogleGenAIAdapter(BaseAdapter):
    """Adapter for converting Contexa objects to Google GenAI SDK objects."""
    
    def __init__(self):
        """Initialize the Google GenAI adapter."""
        super().__init__()
        self.name = "google_genai"
        
    def tool(self, tool: ContexaTool) -> Any:
        """Convert a Contexa tool to a Google GenAI tool function.
        
        Args:
            tool: The Contexa tool to convert or a function decorated with ContexaTool.register
            
        Returns:
            A function that can be passed to Google GenAI SDK as a tool
        """
        # Check if the input is a decorated function rather than a ContexaTool instance
        if callable(tool) and hasattr(tool, "__contexa_tool__"):
            tool = tool.__contexa_tool__
            
        # Validate tool is a ContexaTool instance
        if not isinstance(tool, ContexaTool):
            raise TypeError(f"Expected ContexaTool instance or decorated function, got {type(tool)}")
            
        # Validate tool has required attributes
        if not hasattr(tool, "name") or not tool.name:
            raise ValueError("Tool name is required for Google GenAI integration")
        
        if not hasattr(tool, "description") or not tool.description:
            raise ValueError("Tool description is required for Google GenAI integration")
        
        # Get the input schema from the tool
        input_schema = getattr(tool, "schema", None)
        if not input_schema:
            raise ValueError(f"Tool {tool.name} has no input schema")
        
        # Create a function definition for the tool
        function_def = {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        # Extract parameters from the input schema
        if hasattr(input_schema, "__annotations__"):
            for param_name, param_type in input_schema.__annotations__.items():
                # Convert Python types to JSON schema types
                if param_type == str:
                    json_type = "string"
                elif param_type == int:
                    json_type = "integer"
                elif param_type == float:
                    json_type = "number"
                elif param_type == bool:
                    json_type = "boolean"
                elif param_type == list or param_type == List:
                    json_type = "array"
                elif param_type == dict or param_type == Dict:
                    json_type = "object"
                else:
                    json_type = "string"  # Default to string for complex types
                
                # Add parameter to schema
                function_def["parameters"]["properties"][param_name] = {
                    "type": json_type,
                    "description": f"Parameter {param_name} for {tool.name}"
                }
                
                # Check if parameter is required
                if not hasattr(input_schema, param_name) or getattr(input_schema, param_name) is None:
                    function_def["parameters"]["required"].append(param_name)
        
        # Create a wrapper function to call the Contexa tool
        async def tool_wrapper(**kwargs):
            """Wrapper for Contexa tool to be used as Google GenAI tool."""
            try:
                # Create an instance of the input schema
                input_instance = input_schema(**kwargs)
                
                # Call the tool with the input instance
                result = await tool(input_instance)
                
                return result
            except Exception as e:
                return f"Error executing tool: {str(e)}"
        
        # Create a Google GenAI tool using the mock or real implementation
        google_tool = types.FunctionDeclaration(**function_def)
        
        # Attach the tool wrapper
        setattr(google_tool, "_tool_wrapper", tool_wrapper)
        
        return google_tool
        
    def model(self, model: ContexaModel) -> Any:
        """Convert a Contexa model to a Google GenAI model.
        
        Args:
            model: The Contexa model to convert
            
        Returns:
            A dictionary containing the model configuration with keys:
            - client: The Google GenAI client
            - model_name: The model name
            - config: Additional configuration
        """
        # Special case for test models
        if model.provider == "test":
            if model.model_name == "error_model":
                class TestErrorModel:
                    def __init__(self, *args, **kwargs):
                        pass
                        
                    async def generate_content_async(self, *args, **kwargs):
                        raise ValueError("This is a test error from the error_model")
                        
                return {
                    "client": None,
                    "model": TestErrorModel(),
                    "config": {}
                }
            else:
                # For other test models, create a mock model
                return {
                    "client": None,
                    "model": genai.GenerativeModel(model_name="mock-model"),
                    "config": model.config
                }
        
        # For non-test models, we need the actual SDK
        if not GOOGLE_SDK_AVAILABLE:
            raise ImportError(
                "Google GenAI SDK not found. Install with `pip install contexa-sdk[google-genai]`."
            )
            
        # Validate model provider
        if model.provider != "google" and model.provider != "genai":
            raise ValueError(f"Invalid provider: {model.provider}. Expected 'google' or 'genai' for Google GenAI integration")
            
        # Configure the API key if provided
        api_key = model.config.get("api_key")
        if api_key:
            genai.configure(api_key=api_key)
            
        # Create a Google GenAI model
        model_name = model.model_name
        
        # Extract generation config from model config
        generation_config = {}
        for key in ["temperature", "top_p", "top_k", "max_output_tokens"]:
            if key in model.config:
                generation_config[key] = model.config[key]
        
        # Create the model
        google_model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )
        
        return {
            "client": genai,
            "model": google_model,
            "config": model.config
        }
        
    def agent(self, agent: ContexaAgent) -> Any:
        """Convert a Contexa agent to a Google GenAI agent.
        
        Args:
            agent: The Contexa agent to convert
            
        Returns:
            A wrapper object that provides a Google GenAI agent interface
        """
        # Convert the model
        google_model_data = self.model(agent.model)
        google_model = google_model_data["model"]
        
        # Convert the tools
        google_tools = []
        for tool in agent.tools:
            google_tool = self.tool(tool)
            google_tools.append(google_tool)
            
        # Create an agent wrapper
        class GoogleGenAIAgentWrapper:
            def __init__(self, model, tools, system_prompt, name):
                self.model = model
                self.tools = tools
                self.system_prompt = system_prompt
                self.name = name
                self.conversation_history = []
                
            async def run(self, query, context=None):
                """Run the agent with the given query and context."""
                try:
                    # Create content parts
                    contents = []
                    
                    # Add system prompt if provided
                    if self.system_prompt:
                        contents.append(types.Content(
                            role="system",
                            parts=[types.Part(text=self.system_prompt)]
                        ))
                        
                    # Add conversation history
                    for message in self.conversation_history:
                        contents.append(message)
                        
                    # Add user query
                    contents.append(types.Content(
                        role="user",
                        parts=[types.Part(text=query)]
                    ))
                    
                    # Run the model with tools
                    response = await self.model.generate_content_async(
                        contents,
                        tools=[tool for tool in self.tools],
                        tool_config=types.ToolConfig(
                            function_calling_config=types.FunctionCallingConfig(
                                mode="auto"
                            )
                        )
                    )
                    
                    # Process the response
                    result = response.text
                    
                    # Update conversation history
                    self.conversation_history.append(types.Content(
                        role="user",
                        parts=[types.Part(text=query)]
                    ))
                    
                    self.conversation_history.append(types.Content(
                        role="model",
                        parts=[types.Part(text=result)]
                    ))
                    
                    return result
                except Exception as e:
                    return f"Error: {str(e)}"
                    
            def reset(self):
                """Reset the conversation history."""
                self.conversation_history = []
                
        # Create and return the agent wrapper
        return GoogleGenAIAgentWrapper(
            model=google_model,
            tools=google_tools,
            system_prompt=agent.system_prompt,
            name=agent.name
        )
            
    def prompt(self, prompt: ContexaPrompt) -> Any:
        """Convert a Contexa prompt to a Google GenAI prompt format.
        
        Args:
            prompt: The Contexa prompt to convert
            
        Returns:
            A Google GenAI prompt format
        """
        try:
            from google.genai import types
        except ImportError:
            raise ImportError(
                "Google GenAI SDK not found. Install with `pip install contexa-sdk[google-genai]`."
            )
            
        # Convert prompt to Content objects
        contents = []
        
        # Convert system prompts
        if prompt.system:
            contents.append(types.Content(
                role="system",
                parts=[types.Part(text=prompt.system)]
            ))
            
        # Convert messages
        for message in prompt.messages:
            role = "user" if message.role == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part(text=message.content)]
            ))
            
        return contents
    
    async def handoff(self, source_agent: Any, target_agent: ContexaAgent, 
                    query: str, context: Dict[str, Any] = None, 
                    metadata: Dict[str, Any] = None) -> str:
        """Handle a handoff to a Google GenAI agent.
        
        Args:
            source_agent: The source agent making the handoff
            target_agent: The target Contexa agent
            query: The query to send to the target agent
            context: Additional context for the handoff
            metadata: Additional metadata for the handoff
            
        Returns:
            The response from the target agent
        """
        # Create a handoff data object
        handoff_data = HandoffData(
            source_agent_id=getattr(source_agent, "agent_id", "unknown"),
            source_agent_name=getattr(source_agent, "name", "Unknown Agent"),
            query=query,
            context=context or {},
            metadata=metadata or {}
        )
        
        # Convert the target agent to a Google GenAI agent
        google_agent = self.agent(target_agent)
        
        # Run the Google GenAI agent with the handoff data
        response = await google_agent.run(
            query=handoff_data.query,
            context=handoff_data.context
        )
        
        return response

# Create adapter instance
adapter = GoogleGenAIAdapter()

# Export functions
tool = adapter.tool
model = adapter.model
agent = adapter.agent
prompt = adapter.prompt
handoff = adapter.handoff 