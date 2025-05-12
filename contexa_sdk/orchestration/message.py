"""
Message passing system for agent communication.

This module provides messaging capabilities between agents, including:
- Direct messages between agents
- Broadcast messages to multiple agents
- Communication channels for organized message exchange
"""

import time
import uuid
from typing import Dict, Any, List, Optional, Union


class Message:
    """Message for communication between agents.
    
    Messages represent discrete units of communication between agents,
    similar to messages in human communication systems.
    
    Attributes:
        sender_id (str): ID of the sending agent
        recipient_id (str): ID of the receiving agent
        content (Any): Content of the message - can be string or structured data
        message_type (str): Type/category of message (e.g., "request", "response")
        message_id (str): Unique ID for the message
        timestamp (float): Time when message was created
        metadata (Dict): Additional information about the message
        
    Example:
        ```python
        # Create a message
        msg = Message(
            sender_id="research_agent",
            recipient_id="writing_agent",
            content="Here are the research results",
            message_type="data_transfer",
            metadata={"priority": "high", "source": "database_query"}
        )
        ```
    """
    
    def __init__(
        self,
        sender_id: str,
        recipient_id: str,
        content: Any,
        message_type: str = "default",
        message_id: str = None,
        timestamp: float = None,
        metadata: Dict[str, Any] = None
    ):
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.content = content
        self.message_type = message_type
        self.message_id = message_id or str(uuid.uuid4())
        self.timestamp = timestamp or time.time()
        self.metadata = metadata or {}


class Channel:
    """Channel for message exchange between agents.
    
    Channels provide a way to organize message exchange between agents,
    similar to communication channels in human organizations.
    
    Attributes:
        name (str): Name of the channel
        messages (List[Message]): Messages sent through the channel
        channel_id (str): Unique identifier for the channel
        metadata (Dict): Additional information about the channel
        
    Example:
        ```python
        # Create a channel
        research_channel = Channel(name="research_collaboration")
        
        # Send a message through the channel
        research_channel.send(Message(
            sender_id="researcher_1",
            recipient_id="researcher_2",
            content="Have you seen the latest paper on quantum computing?"
        ))
        
        # Receive messages for a specific agent
        messages = research_channel.receive(recipient_id="researcher_2")
        ```
    """
    
    def __init__(
        self,
        name: str = "default",
        channel_id: str = None,
        metadata: Dict[str, Any] = None
    ):
        self.name = name
        self.messages: List[Message] = []
        self.channel_id = channel_id or str(uuid.uuid4())
        self.metadata = metadata or {}
        
    def send(self, message: Message) -> str:
        """Send a message through the channel
        
        Args:
            message: The message to send
            
        Returns:
            The message ID
        """
        self.messages.append(message)
        return message.message_id
        
    def receive(
        self,
        recipient_id: str,
        sender_id: str = None,
        message_type: str = None,
        since_timestamp: float = None,
        limit: int = None
    ) -> List[Message]:
        """Receive messages from the channel
        
        Args:
            recipient_id: ID of the recipient to filter messages for
            sender_id: Optional sender ID to filter by
            message_type: Optional message type to filter by
            since_timestamp: Optional timestamp to get messages since
            limit: Optional maximum number of messages to return
            
        Returns:
            List of messages matching the filters
        """
        # Start with messages for this recipient
        filtered = [m for m in self.messages if m.recipient_id == recipient_id]
        
        # Apply additional filters if provided
        if sender_id:
            filtered = [m for m in filtered if m.sender_id == sender_id]
            
        if message_type:
            filtered = [m for m in filtered if m.message_type == message_type]
            
        if since_timestamp:
            filtered = [m for m in filtered if m.timestamp > since_timestamp]
            
        # Sort by timestamp (newest messages last)
        filtered.sort(key=lambda m: m.timestamp)
        
        # Apply limit if specified
        if limit and limit > 0:
            filtered = filtered[:limit]
            
        return filtered
        
    def broadcast(
        self,
        sender_id: str,
        recipient_ids: List[str],
        content: Any,
        message_type: str = "broadcast",
        metadata: Dict[str, Any] = None
    ) -> List[str]:
        """Send the same message to multiple recipients
        
        Args:
            sender_id: ID of the sending agent
            recipient_ids: List of recipient agent IDs
            content: Content to send
            message_type: Type of message
            metadata: Additional metadata for the messages
            
        Returns:
            List of message IDs created
        """
        message_ids = []
        
        for recipient_id in recipient_ids:
            msg = Message(
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=content,
                message_type=message_type,
                metadata=metadata
            )
            self.send(msg)
            message_ids.append(msg.message_id)
            
        return message_ids
        
    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Retrieve a specific message by ID
        
        Args:
            message_id: ID of the message to retrieve
            
        Returns:
            The message if found, None otherwise
        """
        for msg in self.messages:
            if msg.message_id == message_id:
                return msg
        return None
        
    def clear(self) -> None:
        """Clear all messages from the channel"""
        self.messages = [] 