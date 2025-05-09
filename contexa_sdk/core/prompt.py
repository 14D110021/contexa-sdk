"""Prompt module for Contexa SDK.

This module provides a framework-agnostic way to define, manage, and format prompts
for language models. It supports Jinja2 templating for dynamic prompt generation
and includes built-in input validation using Pydantic models.

Prompts can be serialized to and from dictionaries for storage and exchange between
components, and include versioning for tracking changes over time.

Examples:
    Create a basic prompt:
    
    ```python
    from contexa_sdk.core.prompt import ContexaPrompt
    
    # Create a prompt with Jinja2 template
    prompt = ContexaPrompt(
        template="Hello, {{ name }}! How can I help you with {{ topic }}?",
        name="greeting_prompt",
        description="A greeting prompt that includes the user's name and topic"
    )
    
    # Format the prompt with values
    formatted = prompt.format(name="Alice", topic="Python programming")
    print(formatted)  # "Hello, Alice! How can I help you with Python programming?"
    ```
    
    Create a prompt with input validation:
    
    ```python
    from contexa_sdk.core.prompt import ContexaPrompt
    from pydantic import BaseModel
    
    class GreetingInput(BaseModel):
        name: str
        topic: str
    
    prompt = ContexaPrompt(
        template="Hello, {{ name }}! How can I help you with {{ topic }}?",
        name="validated_greeting",
        description="A greeting prompt with validated inputs",
        input_schema=GreetingInput
    )
    
    # This will validate inputs before formatting
    formatted = prompt.format(name="Bob", topic="AI")
    ```
"""

import uuid
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from jinja2 import Template

from contexa_sdk.core.config import ContexaConfig


class ContexaPrompt:
    """Framework-agnostic wrapper for prompts.
    
    ContexaPrompt represents a template-based prompt that can be formatted with
    variables. It supports Jinja2 templating for complex dynamic prompts and
    optional input validation using Pydantic models.
    
    Prompts can be used to generate consistent system instructions, user queries,
    or structured content for language models across different frameworks.
    
    Attributes:
        template (str): The Jinja2 template string for the prompt
        name (str): Name of the prompt for identification
        description (str): Description of what the prompt does
        version (str): Version string for tracking changes
        config (ContexaConfig): Configuration options for the prompt
        prompt_id (str): Unique identifier for the prompt instance
        input_schema (type[BaseModel]): Optional Pydantic model for input validation
    """
    
    def __init__(
        self,
        template: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        version: str = "0.1.0",
        config: Optional[ContexaConfig] = None,
        prompt_id: Optional[str] = None,
        input_schema: Optional[type[BaseModel]] = None,
    ):
        """Initialize a ContexaPrompt.
        
        Args:
            template: Jinja2 template string
            name: Name of the prompt
            description: Description of the prompt
            version: Version of the prompt
            config: Configuration for the prompt
            prompt_id: Unique ID for the prompt (auto-generated if not provided)
            input_schema: Pydantic model for input validation
        """
        self.template = template
        self.name = name or "unnamed_prompt"
        self.description = description or ""
        self.version = version
        self.config = config or ContexaConfig()
        self.prompt_id = prompt_id or str(uuid.uuid4())
        self.input_schema = input_schema
        
        # Compile the template
        self._jinja_template = Template(template)
        
    def format(self, **kwargs: Any) -> str:
        """Format the prompt with the given variables.
        
        Renders the Jinja2 template with the provided variables. If an input_schema
        is defined, the inputs will be validated against the schema before formatting.
        
        Args:
            **kwargs: Variables to use in formatting the template
            
        Returns:
            str: The formatted prompt string
            
        Raises:
            ValidationError: If input validation fails against the input_schema
        """
        # Validate inputs if schema provided
        if self.input_schema:
            validated = self.input_schema(**kwargs)
            kwargs = validated.model_dump()
            
        return self._jinja_template.render(**kwargs)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the prompt to a dictionary.
        
        Serializes the prompt to a dictionary representation that can be stored
        or transmitted. Includes the input schema if one was defined.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the prompt
        """
        result = {
            "name": self.name,
            "description": self.description,
            "template": self.template,
            "version": self.version,
            "prompt_id": self.prompt_id,
        }
        
        if self.input_schema:
            result["input_schema"] = self.input_schema.model_json_schema()
            
        return result
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContexaPrompt":
        """Create a prompt from a dictionary.
        
        Deserializes a prompt from a dictionary representation, including
        reconstructing the input schema if one was included.
        
        Args:
            data (Dict[str, Any]): Dictionary representation of a prompt
            
        Returns:
            ContexaPrompt: The reconstructed prompt object
        """
        # Handle input schema if provided
        input_schema = None
        if "input_schema" in data and data["input_schema"]:
            from pydantic.json_schema import model_from_json_schema
            input_schema = model_from_json_schema(
                schema=data["input_schema"],
                model_name=f"{data.get('name', 'Unnamed')}Input"
            )
            
        return cls(
            template=data["template"],
            name=data.get("name"),
            description=data.get("description"),
            version=data.get("version", "0.1.0"),
            prompt_id=data.get("prompt_id"),
            input_schema=input_schema,
        )
        
    @staticmethod
    def system_prompt(content: str) -> "ContexaPrompt":
        """Create a simple system prompt.
        
        Convenience method to create a prompt intended to be used as a system
        message for a language model.
        
        Args:
            content (str): The system prompt content
            
        Returns:
            ContexaPrompt: A prompt object configured as a system prompt
            
        Example:
            ```python
            system = ContexaPrompt.system_prompt(
                "You are a helpful assistant specialized in Python programming."
            )
            ```
        """
        return ContexaPrompt(
            template=content,
            name="system_prompt",
            description="System prompt",
        )
        
    @staticmethod
    def user_prompt(content: str) -> "ContexaPrompt":
        """Create a simple user prompt.
        
        Convenience method to create a prompt intended to be used as a user
        message for a language model.
        
        Args:
            content (str): The user prompt content
            
        Returns:
            ContexaPrompt: A prompt object configured as a user prompt
            
        Example:
            ```python
            user = ContexaPrompt.user_prompt(
                "Can you explain how to use decorators in Python?"
            )
            ```
        """
        return ContexaPrompt(
            template=content,
            name="user_prompt",
            description="User prompt",
        ) 