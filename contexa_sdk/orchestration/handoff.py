"""
Task handoff system for agent delegation and collaboration.

This module provides structures for formal task handoffs between agents,
including validation, tracking, and protocol enforcement.
"""

import time
import uuid
from typing import Dict, Any, List, Optional, Type, Union
from pydantic import BaseModel, ValidationError

class HandoffProtocol:
    """Protocol for structured agent interactions.
    
    Protocols define the expected format and validation rules for
    data exchanges between agents, similar to API contracts.
    
    Attributes:
        name (str): Name of the protocol
        input_schema (Type[BaseModel], optional): Pydantic model for input validation
        output_schema (Type[BaseModel], optional): Pydantic model for output validation
        protocol_id (str): Unique identifier for the protocol
        description (str): Human-readable description of the protocol
        
    Example:
        ```python
        from pydantic import BaseModel, Field
        
        class ResearchQuery(BaseModel):
            topic: str
            max_results: int = Field(ge=1, le=100)
            
        class ResearchResult(BaseModel):
            findings: List[Dict[str, Any]]
            sources: List[str]
            confidence: float = Field(ge=0.0, le=1.0)
            
        # Create a protocol
        research_protocol = HandoffProtocol(
            name="research_protocol",
            input_schema=ResearchQuery,
            output_schema=ResearchResult,
            description="Protocol for research requests and results"
        )
        ```
    """
    
    def __init__(
        self,
        name: str,
        input_schema: Type[BaseModel] = None,
        output_schema: Type[BaseModel] = None,
        protocol_id: str = None,
        description: str = ""
    ):
        self.name = name
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.protocol_id = protocol_id or str(uuid.uuid4())
        self.description = description
        
    def validate_input(self, data: Dict[str, Any]) -> Any:
        """Validate input data against the input schema
        
        Args:
            data: Data to validate
            
        Returns:
            Validated data (as Pydantic model if schema exists, otherwise as is)
            
        Raises:
            ValidationError: If data doesn't match the schema
        """
        if self.input_schema:
            return self.input_schema(**data)
        return data
        
    def validate_output(self, data: Dict[str, Any]) -> Any:
        """Validate output data against the output schema
        
        Args:
            data: Data to validate
            
        Returns:
            Validated data (as Pydantic model if schema exists, otherwise as is)
            
        Raises:
            ValidationError: If data doesn't match the schema
        """
        if self.output_schema:
            return self.output_schema(**data)
        return data


class TaskHandoff:
    """Formal task transfer between agents.
    
    TaskHandoff represents a structured workflow for delegating tasks between 
    agents, with optional protocol validation and tracking of results.
    
    Attributes:
        sender: The agent sending the task
        recipient: The agent receiving the task
        task_description (str): Description of the task
        input_data (Dict): Data provided for the task execution
        protocol (HandoffProtocol, optional): Protocol for data validation
        handoff_id (str): Unique identifier for this handoff
        status (str): Current status of the handoff
        created_at (float): Timestamp when handoff was created
        completed_at (float, optional): Timestamp when handoff was completed
        result (Dict, optional): Result of the task execution
        metadata (Dict): Additional information about the handoff
        
    Example:
        ```python
        # Create a handoff
        handoff = TaskHandoff(
            sender=research_agent,
            recipient=validation_agent,
            task_description="Validate these research findings",
            input_data={
                "topic": "Quantum Computing",
                "findings": [...],
                "confidence": 0.85
            },
            protocol=validation_protocol
        )
        
        # Execute the handoff
        result = handoff.execute()
        
        # Check status
        print(f"Status: {handoff.status}")
        if handoff.status == "completed":
            print(f"Result: {handoff.result}")
        ```
    """
    
    def __init__(
        self,
        sender: Any,
        recipient: Any,
        task_description: str,
        input_data: Dict[str, Any],
        protocol: Optional[HandoffProtocol] = None,
        handoff_id: str = None,
        metadata: Dict[str, Any] = None,
        callbacks: Dict[str, callable] = None
    ):
        self.sender = sender
        self.recipient = recipient
        self.task_description = task_description
        self.input_data = input_data
        self.protocol = protocol
        self.handoff_id = handoff_id or str(uuid.uuid4())
        self.status = "created"
        self.created_at = time.time()
        self.completed_at = None
        self.result = None
        self.error = None
        self.metadata = metadata or {}
        self.callbacks = callbacks or {}
        
    def execute(self) -> Dict[str, Any]:
        """Execute the task handoff
        
        This method:
        1. Validates the input if protocol exists
        2. Checks if recipient accepts from sender
        3. Passes the task to the recipient
        4. Validates the output if protocol exists
        5. Updates status and result
        
        Returns:
            Dict with status and results/error information
        """
        try:
            # Check permissions if agent supports it
            if hasattr(self.recipient, 'allowed_incoming_agents'):
                allow_all = "*" in self.recipient.allowed_incoming_agents
                sender_allowed = self.sender.id in self.recipient.allowed_incoming_agents
                
                if not (allow_all or sender_allowed):
                    raise PermissionError(
                        f"Recipient {self.recipient.id} does not accept tasks from {self.sender.id}"
                    )
            
            # Validate input if protocol exists
            validated_input = self.input_data
            if self.protocol:
                try:
                    validated_input = self.protocol.validate_input(self.input_data)
                    # Convert to dict if it's a Pydantic model
                    if hasattr(validated_input, "dict"):
                        validated_input = validated_input.dict()
                except ValidationError as e:
                    self.status = "failed"
                    self.error = f"Input validation failed: {str(e)}"
                    if "on_validation_failed" in self.callbacks:
                        self.callbacks["on_validation_failed"](self, e)
                    return {"status": "failed", "error": self.error}
            
            # Prepare handoff data
            handoff_data = {
                "task_description": self.task_description,
                "input_data": validated_input,
                "handoff_id": self.handoff_id,
                "sender_id": getattr(self.sender, "id", str(self.sender)),
                "protocol": self.protocol.name if self.protocol else None,
                "metadata": self.metadata
            }
            
            # Check if recipient has a specific method for handoffs
            if hasattr(self.recipient, "process_handoff"):
                response = self.recipient.process_handoff(handoff_data)
            else:
                # Fall back to generic run method
                response = self.recipient.run(handoff_data)
            
            # Validate output if protocol exists
            if self.protocol and self.protocol.output_schema and "result" in response:
                try:
                    validated_output = self.protocol.validate_output(response["result"])
                    # Convert to dict if it's a Pydantic model
                    if hasattr(validated_output, "dict"):
                        response["result"] = validated_output.dict()
                except ValidationError as e:
                    self.status = "failed"
                    self.error = f"Output validation failed: {str(e)}"
                    if "on_validation_failed" in self.callbacks:
                        self.callbacks["on_validation_failed"](self, e)
                    return {"status": "failed", "error": self.error}
            
            # Update status and result
            self.completed_at = time.time()
            self.result = response.get("result", response)
            
            if "status" in response:
                self.status = response["status"]
            else:
                self.status = "completed"
                
            # Call completion callback if exists
            if "on_completed" in self.callbacks:
                self.callbacks["on_completed"](self, self.result)
                
            return {
                "status": self.status,
                "handoff_id": self.handoff_id,
                "result": self.result
            }
            
        except Exception as e:
            self.status = "failed"
            self.error = str(e)
            
            # Call error callback if exists
            if "on_error" in self.callbacks:
                self.callbacks["on_error"](self, e)
                
            return {
                "status": "failed",
                "handoff_id": self.handoff_id,
                "error": str(e)
            }
            
    def add_callback(self, event: str, callback: callable) -> None:
        """Add a callback for a specific event
        
        Args:
            event: Event name ('on_completed', 'on_error', 'on_validation_failed')
            callback: Function to call when event occurs
        """
        self.callbacks[event] = callback
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert handoff to dictionary representation
        
        Returns:
            Dictionary with handoff information
        """
        return {
            "handoff_id": self.handoff_id,
            "sender_id": getattr(self.sender, "id", str(self.sender)),
            "recipient_id": getattr(self.recipient, "id", str(self.recipient)),
            "task_description": self.task_description,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "protocol": self.protocol.name if self.protocol else None,
            "metadata": self.metadata
        } 