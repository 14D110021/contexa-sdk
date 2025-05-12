"""
Communication components for agent interactions.

This module defines the basic building blocks for agent-to-agent communication,
including messages and communication channels.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
import uuid
import datetime

class Message:
    """A structured message for communication between agents.
    
    Messages represent the basic unit of communication between agents, similar to
    how emails or chat messages work for humans. Each message has a defined sender,
    recipient, and content, along with metadata for tracking and processing.
    
    Attributes:
        sender_id (str): ID of the agent sending the message
        recipient_id (str): ID of the agent receiving the message
        content (Union[str, Dict, BaseModel]): The actual content being sent
        message_type (str): Type classifier (e.g., "text", "task", "result")
        metadata (Dict[str, Any]): Additional data about the message
        message_id (str): Unique identifier for the message
        timestamp (str): ISO format timestamp of when the message was created
    
    Example:
        ```python
        # Basic text message
        message = Message(
            sender_id="research_agent", 
            recipient_id="validation_agent",
            content="Please review the attached research",
            message_type="request"
        )
        
        # Structured data message
        message = Message(
            sender_id="research_agent",
            recipient_id="validation_agent",
            content={"findings": research_data, "confidence": 0.87},
            message_type="research_result"
        )
        ```
    """
    
    def __init__(
        self,
        sender_id: str,
        recipient_id: str,
        content: Union[str, Dict, BaseModel],
        message_type: str = "text",
        metadata: Dict[str, Any] = None,
        message_id: str = None
    ):
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.content = content
        self.message_type = message_type
        self.metadata = metadata or {}
        self.message_id = message_id or str(uuid.uuid4())
        self.timestamp = datetime.datetime.now().isoformat()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "content": self.content if isinstance(self.content, (str, dict)) else self.content.dict(),
            "message_type": self.message_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class Channel:
    """Communication channel for message exchange between agents.
    
    A Channel serves as a message bus that handles routing of messages between
    agents, handling delivery and storage of messages. It's conceptually similar
    to an email server or chat room where messages are sent and received.
    
    Attributes:
        name (str): Identifier for the channel
        messages (List[Message]): Collection of all messages sent on the channel
    
    Example:
        ```python
        # Create a channel for a research team
        channel = Channel(name="research_team")
        
        # Send a message from one agent to another
        channel.send(Message(
            sender_id="research_agent",
            recipient_id="validation_agent",
            content="Please validate these findings"
        ))
        
        # Recipient retrieves its messages
        messages = channel.receive(recipient_id="validation_agent")
        for msg in messages:
            print(f"From: {msg.sender_id}, Content: {msg.content}")
        ```
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.messages = []
        
    def send(self, message: Message) -> str:
        """Send a message through the channel
        
        Args:
            message: The message to send
            
        Returns:
            The message ID of the sent message
        """
        self.messages.append(message)
        return message.message_id
        
    def receive(self, recipient_id: str, since_timestamp: Optional[str] = None) -> List[Message]:
        """Retrieve messages for a recipient
        
        Args:
            recipient_id: ID of the recipient agent
            since_timestamp: Optional timestamp to only get messages after this time
            
        Returns:
            List of messages addressed to the recipient
        """
        if since_timestamp:
            return [m for m in self.messages 
                   if m.recipient_id == recipient_id and m.timestamp > since_timestamp]
        return [m for m in self.messages if m.recipient_id == recipient_id] 