"""Converters for Google AI integration."""

import asyncio
import json
import inspect
from typing import Any, Dict, List, Optional, Union, Callable

from contexa_sdk.core.tool import BaseTool, RemoteTool
from contexa_sdk.core.model import ContexaModel, ModelMessage
from contexa_sdk.core.agent import ContexaAgent, RemoteAgent
from contexa_sdk.observability import get_logger, trace, SpanKind

# Create a logger for this module
logger = get_logger(__name__)


@trace(kind=SpanKind.INTERNAL)
async def convert_tool_to_google(tool: Union[BaseTool, RemoteTool]) -> Dict[str, Any]:
    """Convert a Contexa tool to Google Vertex AI format.
    
    Args:
        tool: The Contexa tool to convert
        
    Returns:
        Google AI tool specification
    """
    logger.info(f"Converting Contexa tool {tool.name} to Google AI format")
    
    # Create the parameter schema
    properties = {}
    required = []
    
    for name, schema in tool.parameters.items():
        # Copy the schema
        properties[name] = dict(schema)
        
        # Add required parameters to the list
        if schema.get("required", False):
            required.append(name)
    
    # Create the Google function calling format (similar to OpenAI)
    google_tool = {
        "function_declarations": [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "OBJECT",
                    "properties": properties,
                    "required": required,
                },
            }
        ]
    }
    
    return google_tool


@trace(kind=SpanKind.INTERNAL)
async def convert_model_to_google(model: ContexaModel) -> Any:
    """Convert a Contexa model to Google Vertex AI format.
    
    Args:
        model: The Contexa model to convert
        
    Returns:
        Google AI model wrapper
    """
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
    except ImportError:
        logger.error("Google Vertex AI not installed. Please install google-cloud-aiplatform to use this feature.")
        raise ImportError("Google Vertex AI not installed. Please install google-cloud-aiplatform to use this feature.")
    
    logger.info(f"Converting Contexa model {model.model_name} to Google AI model")
    
    # Create a class that wraps the Google model
    class ContexaGoogleAIWrapper:
        """Google AI wrapper for a Contexa model."""
        
        def __init__(self, contexa_model: ContexaModel):
            """Initialize with a Contexa model."""
            self.contexa_model = contexa_model
            self.model_name = contexa_model.model_name
            self.provider = contexa_model.provider
        
        async def generate_content(self, contents, **kwargs) -> Any:
            """Generate content with the model."""
            from vertexai.generative_models import Content, Part
            
            # Convert Google contents to Contexa messages
            contexa_messages = []
            
            # Process the content parts
            for content in contents:
                if isinstance(content, str):
                    # String content is treated as user input
                    contexa_messages.append(ModelMessage(
                        role="user",
                        content=content,
                    ))
                elif hasattr(content, "role") and hasattr(content, "parts"):
                    # Content object with role and parts
                    role = content.role.lower() if hasattr(content.role, "lower") else content.role
                    
                    # Map Google roles to Contexa roles
                    role_map = {
                        "user": "user",
                        "model": "assistant",
                        "system": "system",
                    }
                    
                    contexa_role = role_map.get(role, "user")
                    
                    # Extract text from parts
                    text_parts = []
                    for part in content.parts:
                        if isinstance(part, str):
                            text_parts.append(part)
                        elif hasattr(part, "text"):
                            text_parts.append(part.text)
                    
                    contexa_messages.append(ModelMessage(
                        role=contexa_role,
                        content=" ".join(text_parts),
                    ))
            
            # Generate a response
            response = await self.contexa_model.generate(contexa_messages)
            
            # Convert back to Google format
            from vertexai.generative_models import GenerationResponse, GeneratedContent, Part
            
            # Create a simplified response
            google_response = {
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [
                                {"text": response.content}
                            ]
                        }
                    }
                ],
            }
            
            # Return the response in a format similar to Google's
            return google_response
        
        def generate_content_sync(self, contents, **kwargs) -> Any:
            """Generate content synchronously."""
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.generate_content(contents, **kwargs))
    
    # Create and return the wrapper
    google_model = ContexaGoogleAIWrapper(model)
    return google_model


@trace(kind=SpanKind.INTERNAL)
async def convert_agent_to_google(agent: Union[ContexaAgent, RemoteAgent]) -> Any:
    """Convert a Contexa agent to Google AI Agent format.
    
    Args:
        agent: The Contexa agent to convert
        
    Returns:
        Google AI agent wrapper
    """
    logger.info(f"Converting Contexa agent {agent.name} to Google AI agent")
    
    # Create a class that wraps the Google agent
    class ContexaGoogleAgentWrapper:
        """Google AI wrapper for a Contexa agent."""
        
        def __init__(self, contexa_agent: Union[ContexaAgent, RemoteAgent]):
            """Initialize with a Contexa agent."""
            self.contexa_agent = contexa_agent
        
        async def generate_content(self, contents, **kwargs) -> Any:
            """Generate content with the agent."""
            # Extract the query from the contents
            query = ""
            
            if isinstance(contents, str):
                query = contents
            elif hasattr(contents, "__iter__"):
                for content in contents:
                    if isinstance(content, str):
                        query += content + " "
                    elif hasattr(content, "parts"):
                        for part in content.parts:
                            if isinstance(part, str):
                                query += part + " "
                            elif hasattr(part, "text"):
                                query += part.text + " "
            
            # Run the Contexa agent
            result = await self.contexa_agent.run(query.strip())
            
            # Create a response in Google's format
            return {
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [
                                {"text": result}
                            ]
                        }
                    }
                ],
            }
        
        def generate_content_sync(self, contents, **kwargs) -> Any:
            """Generate content synchronously."""
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.generate_content(contents, **kwargs))
    
    # Create and return the wrapper
    google_agent = ContexaGoogleAgentWrapper(agent)
    return google_agent


@trace(kind=SpanKind.INTERNAL)
async def adapt_google_agent(google_agent: Any) -> RemoteAgent:
    """Adapt a Google AI agent to work with Contexa.
    
    Args:
        google_agent: The Google AI agent to adapt
        
    Returns:
        Contexa RemoteAgent that wraps the Google AI agent
    """
    # Create a wrapper that executes the Google agent
    class GoogleAgentWrapper(RemoteAgent):
        """Wrapper for a Google AI agent."""
        
        def __init__(self, google_agent: Any):
            """Initialize with a Google AI agent."""
            super().__init__(
                endpoint_url="google://agent",  # Dummy endpoint
                name=getattr(google_agent, "name", "Google AI Agent"),
                description=getattr(google_agent, "description", ""),
            )
            self.google_agent = google_agent
        
        async def run(self, query: str, **kwargs) -> str:
            """Run the Google AI agent."""
            try:
                # Generate content with the Google agent
                if hasattr(self.google_agent, "generate_content"):
                    # Check if it's async
                    if asyncio.iscoroutinefunction(self.google_agent.generate_content):
                        response = await self.google_agent.generate_content(query)
                    else:
                        response = self.google_agent.generate_content(query)
                    
                    # Extract the text from the response
                    if hasattr(response, "text"):
                        return response.text
                    elif hasattr(response, "candidates") and len(response.candidates) > 0:
                        candidate = response.candidates[0]
                        if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                            parts = candidate.content.parts
                            if parts and hasattr(parts[0], "text"):
                                return parts[0].text
                    
                    # If we couldn't extract the text in a structured way, try as a string
                    return str(response)
                else:
                    # Fall back to treating it as a callable
                    result = self.google_agent(query)
                    return str(result)
            except Exception as e:
                logger.error(f"Error running Google AI agent: {str(e)}")
                raise
    
    # Create and return the wrapper
    return GoogleAgentWrapper(google_agent) 