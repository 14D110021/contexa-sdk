"""Thread management for OpenAI Assistants integration.

This module provides functionality to map between Contexa memory and OpenAI threads,
allowing seamless conversation persistence during handoffs.
"""

import json
from typing import Any, Dict, List, Optional, Union

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ModelMessage


class ThreadManager:
    """Manages OpenAI threads for Contexa agents."""
    
    def __init__(self, client=None):
        """Initialize the thread manager.
        
        Args:
            client: Optional OpenAI client instance. If not provided, 
                   a new client will be created when needed.
        """
        self._client = client
        self._thread_cache = {}  # agent_id -> thread_id mapping
    
    @property
    def client(self):
        """Get the OpenAI client instance."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI()
            except ImportError:
                raise ImportError("OpenAI Python SDK not found. Install with `pip install openai`.")
        return self._client
    
    def get_thread_for_agent(self, agent: ContexaAgent) -> str:
        """Get an OpenAI thread ID for a Contexa agent.
        
        If the agent doesn't have an associated thread yet, a new one is created.
        
        Args:
            agent: The Contexa agent
            
        Returns:
            The OpenAI thread ID
        """
        # Check if we already have a thread for this agent
        if agent.agent_id in self._thread_cache:
            return self._thread_cache[agent.agent_id]
        
        # Create a new thread
        thread = self.client.beta.threads.create()
        
        # Cache the thread ID
        self._thread_cache[agent.agent_id] = thread.id
        
        # Add thread_id to agent's metadata
        if not hasattr(agent, "metadata"):
            agent.metadata = {}
        agent.metadata["openai_thread_id"] = thread.id
        
        return thread.id
    
    def memory_to_thread(self, agent: ContexaAgent) -> str:
        """Convert agent memory to an OpenAI thread.
        
        Args:
            agent: The Contexa agent with memory to convert
            
        Returns:
            The OpenAI thread ID
        """
        # Get or create a thread
        thread_id = self.get_thread_for_agent(agent)
        
        # Convert memory to thread messages
        messages = []
        
        # Add messages from the agent's memory
        for msg in agent.memory.message_history:
            if msg["role"] in ["user", "assistant", "system"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add messages to the thread
        for msg in messages:
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role=msg["role"],
                content=msg["content"]
            )
        
        return thread_id
    
    def thread_to_memory(self, thread_id: str, agent: ContexaAgent) -> None:
        """Update agent memory from an OpenAI thread.
        
        Args:
            thread_id: The OpenAI thread ID
            agent: The Contexa agent to update
        """
        # Retrieve messages from the thread
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        
        # Clear existing memory (optional, could also merge instead)
        agent.memory.clear()
        
        # Add messages to agent memory
        for msg in messages.data:
            # Convert OpenAI message format to Contexa format
            role = msg.role
            
            # Extract content from OpenAI's content structure
            content = ""
            for content_part in msg.content:
                if content_part.type == "text":
                    content += content_part.text.value
            
            # Add to memory
            if role == "user":
                agent.memory.add_user_message(content)
            elif role == "assistant":
                agent.memory.add_ai_message(content)
            elif role == "system":
                agent.memory.set_system_message(content)
    
    def handoff_to_thread(self, handoff_data: Any, target_assistant_id: str) -> str:
        """Convert a handoff to an OpenAI thread run.
        
        Args:
            handoff_data: Contexa HandoffData object
            target_assistant_id: The OpenAI assistant ID to hand off to
            
        Returns:
            The response from the target assistant
        """
        # Create a new thread or reuse existing
        thread = self.client.beta.threads.create()
        
        # Add the handoff context as system information
        context_msg = (
            f"HANDOFF CONTEXT: Task handed off from agent '{handoff_data.source_agent_name}'. "
            f"Additional context: {json.dumps(handoff_data.context, indent=2)}"
        )
        
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=context_msg
        )
        
        # Add the actual query
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=handoff_data.query
        )
        
        # Run the assistant on the thread
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=target_assistant_id
        )
        
        # Wait for completion
        while run.status in ["queued", "in_progress"]:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        
        # Get the response
        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
        # Get the latest assistant message
        for msg in messages.data:
            if msg.role == "assistant":
                # Extract content from OpenAI's content structure
                content = ""
                for content_part in msg.content:
                    if content_part.type == "text":
                        content += content_part.text.value
                return content
        
        return "No response from assistant."


# Create a singleton thread manager
thread_manager = ThreadManager()

# Export functions
def get_thread_for_agent(agent: ContexaAgent) -> str:
    """Get an OpenAI thread ID for a Contexa agent."""
    return thread_manager.get_thread_for_agent(agent)

def memory_to_thread(agent: ContexaAgent) -> str:
    """Convert agent memory to an OpenAI thread."""
    return thread_manager.memory_to_thread(agent)

def thread_to_memory(thread_id: str, agent: ContexaAgent) -> None:
    """Update agent memory from an OpenAI thread."""
    thread_manager.thread_to_memory(thread_id, agent)

def handoff_to_thread(handoff_data: Any, target_assistant_id: str) -> str:
    """Convert a handoff to an OpenAI thread run."""
    return thread_manager.handoff_to_thread(handoff_data, target_assistant_id) 