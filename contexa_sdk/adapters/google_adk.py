"""Google adapter for converting Contexa objects to Google GenAI SDK objects."""

import inspect
import asyncio
import json
from typing import Any, Dict, List, Optional, Union, Callable

from contexa_sdk.adapters.base import BaseAdapter
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel, ModelMessage
from contexa_sdk.core.agent import ContexaAgent, HandoffData
from contexa_sdk.core.prompt import ContexaPrompt


class GoogleAIAdapter(BaseAdapter):
    """Google adapter for converting Contexa objects to Google GenAI SDK objects."""
    
    def tool(self, tool: ContexaTool) -> Any:
        """Convert a Contexa tool to a Google GenAI tool function.
        
        Args:
            tool: The Contexa tool to convert
            
        Returns:
            A function that can be passed to Google GenAI SDK as a tool
        """
        try:
            from google.genai import types
        except ImportError:
            raise ImportError(
                "Google GenAI SDK not found. Install with `pip install contexa-sdk[google]`."
            )
            
        # Create a sync wrapper function for our async tool
        def google_tool_fn(**kwargs):
            """Function docstring will be replaced."""
            return asyncio.run(tool(**kwargs))
            
        # Update the docstring
        google_tool_fn.__name__ = tool.name
        google_tool_fn.__doc__ = tool.description
        
        return google_tool_fn
        
    def model(self, model: ContexaModel) -> Any:
        """Convert a Contexa model to a Google GenAI model.
        
        Args:
            model: The Contexa model to convert
            
        Returns:
            A Google GenAI model name or object
        """
        try:
            from google import genai
        except ImportError:
            raise ImportError(
                "Google GenAI SDK not found. Install with `pip install contexa-sdk[google]`."
            )
            
        # Initialize Google AI SDK client with appropriate credentials
        api_key = model.config.get("api_key", None)
        
        # If it's a Google model, use the appropriate initialization
        if api_key:
            client = genai.Client(api_key=api_key)
        else:
            # Try to use environment variables or application default credentials
            client = genai.Client()
        
        # Return the model name which can be used with the client
        return {
            "client": client,
            "model_name": model.model_name
        }
        
    def agent(self, agent: ContexaAgent) -> Any:
        """Convert a Contexa agent to a Google agent-like wrapper.
        
        Google GenAI doesn't have a specific agent framework like OpenAI,
        so we'll create a wrapper that provides similar functionality.
        
        Args:
            agent: The Contexa agent to convert
            
        Returns:
            A Google agent-like object
        """
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError(
                "Google GenAI SDK not found. Install with `pip install contexa-sdk[google]`."
            )
            
        # Convert the model
        model_info = self.model(agent.model)
        client = model_info["client"]
        model_name = model_info["model_name"]
        
        # Convert the tools
        google_tools = [self.tool(tool) for tool in agent.tools]
        
        # Create a wrapper class that behaves like an agent
        class GoogleAIAgentWrapper:
            def __init__(self, client, model_name, tools, system_prompt, name):
                self.client = client
                self.model_name = model_name
                self.tools = tools
                self.system_prompt = system_prompt
                self.name = name
                
            async def run(self, input_text):
                """Run the agent on the given input."""
                # Prepare the messages
                messages = [
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(input_text)]
                    )
                ]
                
                # If system prompt is provided, add it
                if self.system_prompt:
                    messages.insert(0, types.Content(
                        role="system",
                        parts=[types.Part.from_text(self.system_prompt)]
                    ))
                
                # Generate content with tools
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.model_name,
                    contents=messages,
                    config=types.GenerateContentConfig(
                        tools=self.tools,
                    ),
                )
                
                # Handle tool calls if any
                if hasattr(response, "function_calls") and response.function_calls:
                    # Process function calls - simplified implementation
                    function_results = []
                    for func_call in response.function_calls:
                        function_name = func_call.name
                        for tool in self.tools:
                            if getattr(tool, "__name__", "") == function_name:
                                args = func_call.args
                                result = tool(**args)
                                function_results.append({
                                    "name": function_name,
                                    "output": result
                                })
                    
                    # Create a new message with the tool outputs
                    tool_message = types.Content(
                        role="tool",
                        parts=[types.Part.from_text(json.dumps(function_results))]
                    )
                    
                    # Append all messages and the tool results
                    messages.append(response.candidates[0].content)
                    messages.append(tool_message)
                    
                    # Generate final response after tool use
                    final_response = await asyncio.to_thread(
                        self.client.models.generate_content,
                        model=self.model_name,
                        contents=messages,
                    )
                    
                    return final_response.text
                
                # If no tool calls, return the response directly
                return response.text
        
        # Create the agent wrapper
        google_agent = GoogleAIAgentWrapper(
            client=client,
            model_name=model_name,
            tools=google_tools,
            system_prompt=agent.system_prompt,
            name=agent.name,
        )
        
        # Store the original Contexa agent for reference and handoff support
        google_agent.__contexa_agent__ = agent
        
        return google_agent
        
    def prompt(self, prompt: ContexaPrompt) -> Any:
        """Convert a Contexa prompt to a format usable by Google GenAI SDK.
        
        Args:
            prompt: The Contexa prompt to convert
            
        Returns:
            A string template usable by Google GenAI SDK
        """
        # Google GenAI typically just uses string templates
        return prompt.template
    
    async def handoff_to_google_agent(
        self,
        source_agent: ContexaAgent,
        target_agent: Any,  # Google agent wrapper
        query: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Handle handoff to a Google agent.
        
        Args:
            source_agent: The Contexa agent handing off the task
            target_agent: The Google agent wrapper to hand off to
            query: The query to send to the target agent
            context: Additional context to pass to the target agent
            metadata: Additional metadata for the handoff
            
        Returns:
            The target agent's response
        """
        # Check if the target agent is a Google agent wrapper
        if not hasattr(target_agent, "__contexa_agent__"):
            raise TypeError("target_agent must be a Google agent wrapper created by this adapter")
            
        # Create handoff data
        handoff_data = HandoffData(
            query=query,
            context=context or {},
            metadata=metadata or {},
            source_agent_id=source_agent.agent_id,
            source_agent_name=source_agent.name,
        )
        
        # Add context from the source agent's memory
        handoff_data.context["source_agent_memory"] = source_agent.memory.to_dict()
        
        # Record the handoff in the source agent's memory
        source_agent.memory.add_handoff(handoff_data)
        
        # Format the query to include handoff context
        context_str = json.dumps(handoff_data.context, indent=2)
        enhanced_query = (
            f"[Task handoff from agent '{source_agent.name}']\n\n"
            f"CONTEXT: {context_str}\n\n"
            f"TASK: {query}"
        )
        
        # Run the target agent with the enhanced query
        response = await target_agent.run(enhanced_query)
        
        # Update the handoff data with the result
        handoff_data.result = response
        
        # Update the Contexa agent associated with the Google agent if it exists
        target_contexa_agent = target_agent.__contexa_agent__
        target_contexa_agent.receive_handoff(handoff_data)
            
        return response


# Create a singleton instance
_adapter = GoogleAIAdapter()

# Expose the adapter methods at the module level
tool = _adapter.tool
model = _adapter.model
agent = _adapter.agent
prompt = _adapter.prompt

# Expose handoff method at the module level
async def handoff(
    source_agent: ContexaAgent,
    target_agent: Any,
    query: str,
    context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Handle handoff from a Contexa agent to a Google agent."""
    return await _adapter.handoff_to_google_agent(
        source_agent=source_agent,
        target_agent=target_agent,
        query=query,
        context=context,
        metadata=metadata,
    ) 