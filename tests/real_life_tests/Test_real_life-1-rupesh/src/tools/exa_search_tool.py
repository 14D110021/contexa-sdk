"""
Exa Search Tool for CodeMaster Pro

This module provides integration with Exa for intelligent web search capabilities.
Designed to work with both OpenAI agents and Contexa SDK.

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


class ExaSearchInput(BaseModel):
    """Input schema for Exa web search."""
    
    query: str = Field(
        description="Search query for finding relevant technical content",
        examples=["Python async programming best practices", "React hooks tutorial", "FastAPI authentication"]
    )
    num_results: Optional[int] = Field(
        default=5,
        description="Number of search results to return",
        ge=1,
        le=20
    )
    search_type: Optional[str] = Field(
        default="neural",
        description="Type of search to perform",
        enum=["neural", "keyword", "auto"]
    )
    include_domains: Optional[List[str]] = Field(
        default=None,
        description="Specific domains to include in search",
        examples=[["stackoverflow.com", "github.com"], ["docs.python.org"]]
    )
    exclude_domains: Optional[List[str]] = Field(
        default=None,
        description="Domains to exclude from search",
        examples=[["spam.com", "ads.com"]]
    )


class ExaSearchResult(BaseModel):
    """Individual search result from Exa."""
    
    title: str = Field(description="Title of the search result")
    url: str = Field(description="URL of the search result")
    content: str = Field(description="Content snippet from the result")
    published_date: Optional[str] = Field(description="Publication date if available")
    author: Optional[str] = Field(description="Author if available")
    score: float = Field(description="Relevance score for the result")


class ExaSearchOutput(BaseModel):
    """Output schema for Exa search results."""
    
    query: str = Field(description="Original search query")
    results: List[ExaSearchResult] = Field(description="List of search results")
    total_results: int = Field(description="Total number of results found")
    search_type: str = Field(description="Type of search performed")
    success: bool = Field(description="Whether the search was successful")
    error_message: Optional[str] = Field(description="Error message if search failed")
    cost_info: Optional[Dict[str, Any]] = Field(description="Cost information if available")


class ExaSearchTool:
    """
    Exa web search tool.
    
    This tool provides intelligent web search capabilities through the Exa API.
    It's designed to be framework-agnostic and work with both OpenAI and Contexa agents.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Exa search tool.
        
        Args:
            api_key: Optional API key for Exa (if required)
        """
        self.api_key = api_key
        self.name = "exa_web_search"
        self.description = "Search the web for technical content and solutions using Exa's intelligent search"
        
    async def perform_search(
        self,
        query: str,
        num_results: int = 5,
        search_type: str = "neural",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform a web search using Exa.
        
        Args:
            query: Search query
            num_results: Number of results to return
            search_type: Type of search to perform
            include_domains: Domains to include
            exclude_domains: Domains to exclude
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            # This would typically call the actual Exa API
            # For testing purposes, we'll return mock search results
            
            # Mock search results based on common programming queries
            mock_results = {
                "python async": [
                    {
                        "title": "Getting Started With Async Features in Python",
                        "url": "https://realpython.com/python-async-features/",
                        "content": "Learn about asynchronous programming in Python with asyncio, async/await, and best practices for concurrent code execution.",
                        "published_date": "2022-12-16",
                        "author": "Doug Farrell",
                        "score": 0.95
                    },
                    {
                        "title": "Python Asyncio Documentation",
                        "url": "https://docs.python.org/3/library/asyncio.html",
                        "content": "Official Python documentation for asyncio - asynchronous I/O, event loop, coroutines and tasks.",
                        "published_date": "2023-10-01",
                        "author": "Python Software Foundation",
                        "score": 0.92
                    }
                ],
                "react hooks": [
                    {
                        "title": "Introducing Hooks - React Documentation",
                        "url": "https://reactjs.org/docs/hooks-intro.html",
                        "content": "Hooks are a new addition in React 16.8. They let you use state and other React features without writing a class.",
                        "published_date": "2023-11-01",
                        "author": "React Team",
                        "score": 0.98
                    },
                    {
                        "title": "A Complete Guide to useEffect",
                        "url": "https://overreacted.io/a-complete-guide-to-useeffect/",
                        "content": "Deep dive into React's useEffect hook, covering dependencies, cleanup, and common patterns.",
                        "published_date": "2023-08-15",
                        "author": "Dan Abramov",
                        "score": 0.94
                    }
                ],
                "fastapi authentication": [
                    {
                        "title": "FastAPI Security and Authentication",
                        "url": "https://fastapi.tiangolo.com/tutorial/security/",
                        "content": "Learn how to implement security and authentication in FastAPI applications using OAuth2, JWT, and dependencies.",
                        "published_date": "2023-09-20",
                        "author": "Sebastián Ramírez",
                        "score": 0.96
                    }
                ]
            }
            
            # Find relevant mock results
            results = []
            query_lower = query.lower()
            
            for key, mock_data in mock_results.items():
                if any(term in query_lower for term in key.split()):
                    results.extend(mock_data[:num_results])
                    break
            
            # If no specific match, create generic results
            if not results:
                results = [
                    {
                        "title": f"Search Results for: {query}",
                        "url": f"https://example.com/search?q={query.replace(' ', '+')}",
                        "content": f"This is a mock search result for '{query}'. In a real implementation, this would contain actual search results from Exa.",
                        "published_date": "2023-12-01",
                        "author": "Mock Author",
                        "score": 0.85
                    }
                ]
            
            # Limit results to requested number
            results = results[:num_results]
            
            return {
                "results": results,
                "total_results": len(results),
                "success": True,
                "error_message": None,
                "cost_info": {
                    "total": 0.008,
                    "search": {"neural": 0.005},
                    "contents": {"text": 0.003}
                }
            }
            
        except Exception as e:
            logger.error(f"Error performing Exa search for '{query}': {e}")
            return {
                "results": [],
                "total_results": 0,
                "success": False,
                "error_message": str(e),
                "cost_info": None
            }
    
    async def execute(self, input_data: ExaSearchInput) -> ExaSearchOutput:
        """
        Execute the Exa web search.
        
        Args:
            input_data: Input parameters for the search
            
        Returns:
            ExaSearchOutput containing the search results
        """
        try:
            # Perform the search
            search_result = await self.perform_search(
                query=input_data.query,
                num_results=input_data.num_results,
                search_type=input_data.search_type,
                include_domains=input_data.include_domains,
                exclude_domains=input_data.exclude_domains
            )
            
            # Convert results to ExaSearchResult objects
            results = []
            for result in search_result["results"]:
                results.append(ExaSearchResult(
                    title=result["title"],
                    url=result["url"],
                    content=result["content"],
                    published_date=result.get("published_date"),
                    author=result.get("author"),
                    score=result["score"]
                ))
            
            return ExaSearchOutput(
                query=input_data.query,
                results=results,
                total_results=search_result["total_results"],
                search_type=input_data.search_type,
                success=search_result["success"],
                error_message=search_result["error_message"],
                cost_info=search_result["cost_info"]
            )
            
        except Exception as e:
            logger.error(f"Error executing Exa search tool: {e}")
            return ExaSearchOutput(
                query=input_data.query,
                results=[],
                total_results=0,
                search_type=input_data.search_type,
                success=False,
                error_message=f"Tool execution error: {str(e)}",
                cost_info=None
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
                    "query": {
                        "type": "string",
                        "description": "Search query for finding relevant technical content"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of search results to return (default: 5)",
                        "minimum": 1,
                        "maximum": 20
                    },
                    "search_type": {
                        "type": "string",
                        "description": "Type of search to perform",
                        "enum": ["neural", "keyword", "auto"]
                    },
                    "include_domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific domains to include in search"
                    },
                    "exclude_domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Domains to exclude from search"
                    }
                },
                "required": ["query"]
            }
        }


# Convenience function for direct usage
async def search_web(
    query: str,
    num_results: int = 5,
    search_type: str = "neural",
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    api_key: Optional[str] = None
) -> ExaSearchOutput:
    """
    Convenience function for performing web search.
    
    Args:
        query: Search query
        num_results: Number of results to return
        search_type: Type of search to perform
        include_domains: Domains to include
        exclude_domains: Domains to exclude
        api_key: Optional API key
        
    Returns:
        ExaSearchOutput with search results
    """
    tool = ExaSearchTool(api_key=api_key)
    input_data = ExaSearchInput(
        query=query,
        num_results=num_results,
        search_type=search_type,
        include_domains=include_domains,
        exclude_domains=exclude_domains
    )
    return await tool.execute(input_data)


# Example usage
if __name__ == "__main__":
    async def test_exa_search_tool():
        """Test the Exa search tool functionality."""
        tool = ExaSearchTool()
        
        # Test Python async search
        result = await search_web("Python async programming best practices", num_results=3)
        print(f"Python Async Search Results:")
        print(f"Success: {result.success}")
        print(f"Total Results: {result.total_results}")
        for i, res in enumerate(result.results, 1):
            print(f"{i}. {res.title}")
            print(f"   URL: {res.url}")
            print(f"   Score: {res.score}")
        
        # Test React hooks search
        result = await search_web("React hooks tutorial", num_results=2)
        print(f"\nReact Hooks Search Results:")
        print(f"Success: {result.success}")
        print(f"Total Results: {result.total_results}")
        for i, res in enumerate(result.results, 1):
            print(f"{i}. {res.title}")
            print(f"   Content: {res.content[:100]}...")
    
    # Run the test
    asyncio.run(test_exa_search_tool()) 