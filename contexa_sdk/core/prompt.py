"""Prompt module for Contexa SDK."""

import uuid
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from jinja2 import Template

from contexa_sdk.core.config import ContexaConfig


class ContexaPrompt:
    """Framework-agnostic wrapper for prompts."""
    
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
        
        Args:
            **kwargs: Variables to use in formatting
            
        Returns:
            The formatted prompt
        """
        # Validate inputs if schema provided
        if self.input_schema:
            validated = self.input_schema(**kwargs)
            kwargs = validated.model_dump()
            
        return self._jinja_template.render(**kwargs)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the prompt to a dictionary."""
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
        """Create a prompt from a dictionary."""
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
        
        Args:
            content: The system prompt content
            
        Returns:
            A ContexaPrompt with the system prompt
        """
        return ContexaPrompt(
            template=content,
            name="system_prompt",
            description="System prompt",
        )
        
    @staticmethod
    def user_prompt(content: str) -> "ContexaPrompt":
        """Create a simple user prompt.
        
        Args:
            content: The user prompt content
            
        Returns:
            A ContexaPrompt with the user prompt
        """
        return ContexaPrompt(
            template=content,
            name="user_prompt",
            description="User prompt",
        ) 