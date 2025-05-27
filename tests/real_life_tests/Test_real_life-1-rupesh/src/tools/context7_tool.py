"""
Context7 Documentation Tool for CodeMaster Pro

This module provides integration with Context7 for real-time library documentation lookup.
Designed to work with both OpenAI and Contexa SDK.

Author: Rupesh Raj
Created: May 2025
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import aiohttp

# Configure logging
logger = logging.getLogger(__name__)


class Context7Input(BaseModel):
    """Input schema for Context7 documentation lookup."""
    
    library_name: str = Field(
        description="Name of the library or framework to look up documentation for",
        examples=["react", "python", "fastapi", "django"]
    )
    topic: Optional[str] = Field(
        default=None,
        description="Specific topic within the library to focus on",
        examples=["hooks", "routing", "authentication", "deployment"]
    )
    max_tokens: Optional[int] = Field(
        default=5000,
        description="Maximum number of tokens to retrieve",
        ge=100,
        le=10000
    )


class Context7Output(BaseModel):
    """Output schema for Context7 documentation results."""
    
    library_id: str = Field(description="Context7-compatible library ID")
    content: str = Field(description="Retrieved documentation content")
    topic: Optional[str] = Field(description="Topic that was searched for")
    tokens_used: int = Field(description="Number of tokens in the response")
    success: bool = Field(description="Whether the lookup was successful")
    error_message: Optional[str] = Field(description="Error message if lookup failed")


class Context7Tool:
    """
    Context7 documentation lookup tool.
    
    This tool provides real-time access to library documentation through the Context7 API.
    It's designed to be framework-agnostic and work with both OpenAI and Contexa agents.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Context7 tool.
        
        Args:
            api_key: Optional API key for Context7 (if required)
        """
        self.api_key = api_key
        self.name = "context7_docs"
        self.description = "Retrieve up-to-date documentation for libraries and frameworks"
        
    async def resolve_library_id(self, library_name: str) -> Optional[str]:
        """
        Resolve a library name to a Context7-compatible library ID.
        
        Args:
            library_name: Name of the library to resolve
            
        Returns:
            Context7-compatible library ID or None if not found
        """
        try:
            # This would typically call the actual Context7 resolve API
            # For now, we'll simulate the resolution process
            
            # Common library mappings
            library_mappings = {
                "react": "/reactjs/react.dev",
                "nextjs": "/vercel/nextjs",
                "fastapi": "/tiangolo/fastapi",
                "django": "/django/django",
                "flask": "/pallets/flask",
                "python": "/python/docs",
                "typescript": "/microsoft/typescript",
                "vue": "/vuejs/vue",
                "angular": "/angular/angular"
            }
            
            # Try direct mapping first
            if library_name.lower() in library_mappings:
                return library_mappings[library_name.lower()]
            
            # For this test, we'll use a mock resolution
            # In real implementation, this would call the actual Context7 API
            logger.info(f"Resolving library ID for: {library_name}")
            return f"/mock/{library_name.lower()}"
            
        except Exception as e:
            logger.error(f"Error resolving library ID for {library_name}: {e}")
            return None
    
    async def get_documentation(
        self, 
        library_id: str, 
        topic: Optional[str] = None,
        max_tokens: int = 5000
    ) -> Dict[str, Any]:
        """
        Retrieve documentation for a specific library.
        
        Args:
            library_id: Context7-compatible library ID
            topic: Optional topic to focus on
            max_tokens: Maximum tokens to retrieve
            
        Returns:
            Dictionary containing documentation content and metadata
        """
        try:
            # This would typically call the actual Context7 API
            # For testing purposes, we'll return mock documentation
            
            mock_docs = {
                "/reactjs/react.dev": {
                    "hooks": "React Hooks are functions that let you use state and other React features in functional components. The most common hooks are useState for managing state and useEffect for side effects.",
                    "components": "React components are the building blocks of React applications. They can be functional or class-based, with functional components being preferred in modern React.",
                    "default": "React is a JavaScript library for building user interfaces. It uses a component-based architecture and virtual DOM for efficient rendering."
                },
                "/tiangolo/fastapi": {
                    "routing": "FastAPI routing is handled through decorators like @app.get(), @app.post(), etc. You can define path parameters, query parameters, and request bodies.",
                    "authentication": "FastAPI supports various authentication methods including OAuth2, JWT tokens, and API keys. Use dependencies for authentication logic.",
                    "default": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints."
                }
            }
            
            # Get documentation content
            if library_id in mock_docs:
                content = mock_docs[library_id].get(topic, mock_docs[library_id]["default"])
            else:
                content = f"Documentation for {library_id} - This is mock documentation content for testing purposes. In a real implementation, this would contain actual library documentation."
            
            # Simulate token counting (rough estimate)
            tokens_used = len(content.split()) * 1.3  # Rough token estimation
            
            return {
                "content": content,
                "tokens_used": int(tokens_used),
                "success": True,
                "error_message": None
            }
            
        except Exception as e:
            logger.error(f"Error retrieving documentation for {library_id}: {e}")
            return {
                "content": "",
                "tokens_used": 0,
                "success": False,
                "error_message": str(e)
            }
    
    async def execute(self, input_data: Context7Input) -> Context7Output:
        """
        Execute the Context7 documentation lookup.
        
        Args:
            input_data: Input parameters for the lookup
            
        Returns:
            Context7Output containing the documentation results
        """
        try:
            # Step 1: Resolve library name to library ID
            library_id = await self.resolve_library_id(input_data.library_name)
            
            if not library_id:
                return Context7Output(
                    library_id="",
                    content="",
                    topic=input_data.topic,
                    tokens_used=0,
                    success=False,
                    error_message=f"Could not resolve library ID for: {input_data.library_name}"
                )
            
            # Step 2: Get documentation
            doc_result = await self.get_documentation(
                library_id=library_id,
                topic=input_data.topic,
                max_tokens=input_data.max_tokens
            )
            
            # Step 3: Return formatted result
            return Context7Output(
                library_id=library_id,
                content=doc_result["content"],
                topic=input_data.topic,
                tokens_used=doc_result["tokens_used"],
                success=doc_result["success"],
                error_message=doc_result["error_message"]
            )
            
        except Exception as e:
            logger.error(f"Error executing Context7 tool: {e}")
            return Context7Output(
                library_id="",
                content="",
                topic=input_data.topic,
                tokens_used=0,
                success=False,
                error_message=f"Tool execution error: {str(e)}"
            )
    
    def get_openai_function_schema(self) -> Dict[str, Any]:
        """
        Get the OpenAI function calling schema for this tool.
        
        Returns:
            Dictionary containing the function schema for OpenAI
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "library_name": {
                        "type": "string",
                        "description": "Name of the library or framework to look up documentation for"
                    },
                    "topic": {
                        "type": "string",
                        "description": "Specific topic within the library to focus on (optional)"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum number of tokens to retrieve (default: 5000)",
                        "minimum": 100,
                        "maximum": 10000
                    }
                },
                "required": ["library_name"]
            }
        }


# Convenience function for direct usage
async def lookup_documentation(
    library_name: str,
    topic: Optional[str] = None,
    max_tokens: int = 5000,
    api_key: Optional[str] = None
) -> Context7Output:
    """
    Convenience function for looking up documentation.
    
    Args:
        library_name: Name of the library to look up
        topic: Optional specific topic
        max_tokens: Maximum tokens to retrieve
        api_key: Optional API key
        
    Returns:
        Context7Output with documentation results
    """
    tool = Context7Tool(api_key=api_key)
    input_data = Context7Input(
        library_name=library_name,
        topic=topic,
        max_tokens=max_tokens
    )
    return await tool.execute(input_data)


# Example usage
if __name__ == "__main__":
    async def test_context7_tool():
        """Test the Context7 tool functionality."""
        tool = Context7Tool()
        
        # Test React documentation lookup
        result = await lookup_documentation("react", "hooks")
        print(f"React Hooks Documentation:")
        print(f"Success: {result.success}")
        print(f"Content: {result.content[:200]}...")
        print(f"Tokens: {result.tokens_used}")
        
        # Test FastAPI documentation lookup
        result = await lookup_documentation("fastapi", "routing")
        print(f"\nFastAPI Routing Documentation:")
        print(f"Success: {result.success}")
        print(f"Content: {result.content[:200]}...")
        print(f"Tokens: {result.tokens_used}")
    
    # Run the test
    asyncio.run(test_context7_tool()) 