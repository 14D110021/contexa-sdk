"""Converters for OpenAI integration."""

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
async def convert_tool_to_openai(tool: Union[BaseTool, RemoteTool]) -> Dict[str, Any]:
    """Convert a Contexa tool to OpenAI format.
    
    Args:
        tool: The Contexa tool to convert
        
    Returns:
        OpenAI tool specification
    """
    logger.info(f"Converting Contexa tool {tool.name} to OpenAI format")
    
    # Create the parameter schema
    properties = {}
    required = []
    
    for name, schema in tool.parameters.items():
        # Copy the schema
        properties[name] = dict(schema)
        
        # Add required parameters to the list
        if schema.get("required", False):
            required.append(name)
    
    # Create the OpenAI function calling format
    openai_tool = {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }
    
    return openai_tool


@trace(kind=SpanKind.INTERNAL)
async def convert_model_to_openai(model: ContexaModel) -> Any:
    """Convert a Contexa model to OpenAI format.
    
    Args:
        model: The Contexa model to convert
        
    Returns:
        OpenAI client
    """
    try:
        import openai
    except ImportError:
        logger.error("OpenAI not installed. Please install openai to use this feature.")
        raise ImportError("OpenAI not installed. Please install openai to use this feature.")
    
    logger.info(f"Converting Contexa model {model.model_name} to OpenAI client")
    
    # Create a class that wraps the OpenAI client
    class ContexaOpenAIWrapper:
        """OpenAI wrapper for a Contexa model."""
        
        def __init__(self, contexa_model: ContexaModel):
            """Initialize with a Contexa model."""
            self.contexa_model = contexa_model
            self.model_name = contexa_model.model_name
            self.provider = contexa_model.provider
            
            # Create a default client
            try:
                self.client = openai.OpenAI()
            except:
                # Older versions of OpenAI
                self.client = openai.Client()
        
        async def chat_completions_create(self, messages: List[Dict[str, str]], **kwargs) -> Any:
            """Create a chat completion."""
            # Convert to Contexa messages
            contexa_messages = []
            for msg in messages:
                from contexa_sdk.core.model import ModelMessage
                contexa_messages.append(ModelMessage(
                    role=msg.get("role", "user"),
                    content=msg.get("content", ""),
                ))
            
            # Generate a response
            response = await self.contexa_model.generate(contexa_messages)
            
            # Convert back to OpenAI format
            from openai.types.chat import ChatCompletion, ChatCompletionMessage
            
            # Create a simplified completion
            completion = {
                "id": "contexa-" + model.model_name,
                "model": model.model_name,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response.content,
                        },
                        "finish_reason": "stop",
                    }
                ],
            }
            
            return completion
    
    # Create and return the wrapper
    openai_wrapper = ContexaOpenAIWrapper(model)
    return openai_wrapper


@trace(kind=SpanKind.INTERNAL)
async def convert_agent_to_openai(agent: Union[ContexaAgent, RemoteAgent]) -> Any:
    """Convert a Contexa agent to OpenAI format.
    
    Currently, there is no direct OpenAI agent equivalent, so we provide a callable wrapper.
    
    Args:
        agent: The Contexa agent to convert
        
    Returns:
        Callable function that acts like an OpenAI assistant
    """
    logger.info(f"Converting Contexa agent {agent.name} to OpenAI callable")
    
    # Create a wrapper function that can be used like an OpenAI assistant run
    class ContexaOpenAIAssistant:
        """Callable wrapper for a Contexa agent that mimics an OpenAI assistant."""
        
        def __init__(self, contexa_agent: Union[ContexaAgent, RemoteAgent]):
            """Initialize with a Contexa agent."""
            self.contexa_agent = contexa_agent
            self.thread_id = f"contexa-{contexa_agent.agent_id}-thread"
            self.assistant_id = f"contexa-{contexa_agent.agent_id}"
        
        async def create_thread(self, **kwargs) -> Dict[str, str]:
            """Create a new thread (stub)."""
            return {"id": self.thread_id}
        
        async def create_message(self, thread_id: str, content: str, **kwargs) -> Dict[str, Any]:
            """Add a message to the thread (stub)."""
            return {
                "id": f"msg_{hash(content)}",
                "thread_id": thread_id,
                "content": content,
                "role": "user",
            }
        
        async def create_run(self, thread_id: str, assistant_id: str, **kwargs) -> Dict[str, Any]:
            """Create and execute a run using the agent."""
            # Get all messages from the thread context
            messages = kwargs.get("messages", [])
            
            # Combine all user messages
            combined_query = ""
            for msg in messages:
                if msg.get("role") == "user":
                    combined_query += msg.get("content", "") + "\n"
            
            if not combined_query and "instructions" in kwargs:
                # Use instructions as the query if no messages
                combined_query = kwargs["instructions"]
            
            # Run the Contexa agent
            try:
                result = await self.contexa_agent.run(combined_query)
                
                # Create and return a run object
                return {
                    "id": f"run_{hash(combined_query)}",
                    "thread_id": thread_id,
                    "assistant_id": assistant_id,
                    "status": "completed",
                    "response": {
                        "role": "assistant",
                        "content": result,
                    },
                }
            except Exception as e:
                logger.error(f"Error running Contexa agent: {str(e)}")
                return {
                    "id": f"run_{hash(combined_query)}",
                    "thread_id": thread_id,
                    "assistant_id": assistant_id,
                    "status": "failed",
                    "error": {
                        "message": str(e),
                    },
                }
        
        async def retrieve_run(self, thread_id: str, run_id: str, **kwargs) -> Dict[str, Any]:
            """Retrieve a run (stub)."""
            # Runs in our implementation are instant, so just return completed
            return {
                "id": run_id,
                "thread_id": thread_id,
                "status": "completed",
            }
        
        async def list_messages(self, thread_id: str, **kwargs) -> Dict[str, Any]:
            """List messages in a thread (stub)."""
            # In our simple implementation, we just return an empty list
            return {
                "data": [],
                "has_more": False,
            }
    
    # Create and return the wrapper
    openai_assistant = ContexaOpenAIAssistant(agent)
    return openai_assistant


@trace(kind=SpanKind.INTERNAL)
async def adapt_openai_assistant(openai_assistant_id: str, openai_client=None) -> RemoteAgent:
    """Adapt an OpenAI assistant to work with Contexa.
    
    Args:
        openai_assistant_id: The ID of the OpenAI assistant
        openai_client: Optional OpenAI client to use
        
    Returns:
        Contexa RemoteAgent that wraps the OpenAI assistant
    """
    try:
        import openai
    except ImportError:
        logger.error("OpenAI not installed. Please install openai to use this feature.")
        raise ImportError("OpenAI not installed. Please install openai to use this feature.")
    
    logger.info(f"Adapting OpenAI assistant {openai_assistant_id}")
    
    # Create the OpenAI client if not provided
    if openai_client is None:
        try:
            openai_client = openai.OpenAI()
        except:
            # Older versions of OpenAI
            openai_client = openai.Client()
    
    # Get the assistant details
    assistant = openai_client.beta.assistants.retrieve(openai_assistant_id)
    
    # Create a wrapper that executes the OpenAI assistant
    class OpenAIAssistantWrapper(RemoteAgent):
        """Wrapper for an OpenAI assistant."""
        
        def __init__(self, assistant_id: str, client):
            """Initialize with an OpenAI assistant ID."""
            super().__init__(
                endpoint_url=f"openai://assistant/{assistant_id}",
                name=assistant.name,
                description=assistant.instructions,
            )
            self.assistant_id = assistant_id
            self.client = client
            self.threads = {}  # Store threads for different conversations
        
        async def run(self, query: str, **kwargs) -> str:
            """Run the OpenAI assistant."""
            try:
                # Get or create a thread for this conversation
                conversation_id = kwargs.get("conversation_id", "default")
                
                if conversation_id not in self.threads:
                    # Create a new thread
                    thread = self.client.beta.threads.create()
                    self.threads[conversation_id] = thread.id
                
                thread_id = self.threads[conversation_id]
                
                # Add the message to the thread
                self.client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=query,
                )
                
                # Run the assistant
                run = self.client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=self.assistant_id,
                )
                
                # Wait for the run to complete
                while run.status in ["queued", "in_progress"]:
                    # Poll for status
                    run = self.client.beta.threads.runs.retrieve(
                        thread_id=thread_id,
                        run_id=run.id,
                    )
                    
                    # Wait before polling again
                    await asyncio.sleep(1)
                
                if run.status != "completed":
                    # Handle failures
                    logger.error(f"OpenAI assistant run failed: {run.status}")
                    return f"Error: Assistant run failed with status {run.status}"
                
                # Get the messages
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread_id,
                    order="desc",
                    limit=1,
                )
                
                # Return the latest assistant message content
                for message in messages.data:
                    if message.role == "assistant":
                        content = []
                        for content_item in message.content:
                            if content_item.type == "text":
                                content.append(content_item.text.value)
                        return "\n".join(content)
                
                return "No response from assistant"
            except Exception as e:
                logger.error(f"Error running OpenAI assistant: {str(e)}")
                raise
    
    # Create and return the wrapper
    return OpenAIAssistantWrapper(openai_assistant_id, openai_client) 