"""Tool module for Contexa SDK."""

import inspect
import uuid
from typing import Any, Callable, Dict, List, Optional, Type, Union, get_type_hints
import asyncio
from functools import wraps

from pydantic import BaseModel, Field, create_model

from contexa_sdk.core.config import ContexaConfig


class ContexaTool:
    """Base class for Contexa tools."""

    name: str
    description: str
    version: str
    schema: Type[BaseModel]
    _func: Callable
    config: ContexaConfig
    tool_id: str
    
    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        version: str = "0.1.0",
        schema: Optional[Type[BaseModel]] = None,
        config: Optional[ContexaConfig] = None,
        tool_id: Optional[str] = None,
        **kwargs,
    ):
        """Initialize a ContexaTool.
        
        Args:
            func: The callable function that implements the tool logic
            name: Name of the tool (defaults to function name)
            description: Description of the tool (defaults to function docstring)
            version: Version of the tool
            schema: Input schema for the tool (generated from type hints if not provided)
            config: Configuration for the tool
            tool_id: Unique ID for the tool (auto-generated if not provided)
        """
        self._func = func
        self.name = name or func.__name__
        self.description = description or (func.__doc__ or "").strip() or f"{self.name} tool"
        self.version = version
        self.config = config or ContexaConfig()
        self.tool_id = tool_id or str(uuid.uuid4())
        
        # Create schema from type hints if not provided
        if schema is None:
            hints = get_type_hints(func)
            if "return" in hints:
                del hints["return"]
            
            # If the first parameter is a BaseModel, use that
            sig = inspect.signature(func)
            first_param = next(iter(sig.parameters.values()), None)
            if first_param and first_param.annotation != inspect.Parameter.empty:
                if issubclass(first_param.annotation, BaseModel):
                    self.schema = first_param.annotation
                    return
            
            # Otherwise generate a schema from type hints
            fields = {}
            for param_name, param in sig.parameters.items():
                if param_name in hints:
                    fields[param_name] = (hints[param_name], ...)
                else:
                    fields[param_name] = (Any, ...)
            
            self.schema = create_model(f"{self.name.title()}Input", **fields)
        else:
            self.schema = schema

    async def __call__(self, **kwargs) -> Any:
        """Call the tool function."""
        # Validate inputs against schema
        inputs = self.schema(**kwargs)
        
        # Check if the function is async
        if inspect.iscoroutinefunction(self._func):
            return await self._func(inputs)
        else:
            # Run sync function in a thread pool
            return await asyncio.to_thread(self._func, inputs)
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert the tool to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "schema": self.schema.model_json_schema(),
            "tool_id": self.tool_id,
        }
        
    @classmethod
    def register(
        cls, 
        name: Optional[str] = None, 
        description: Optional[str] = None,
        version: str = "0.1.0",
    ):
        """Register a function as a ContexaTool.
        
        This decorator can be used to register a function as a ContexaTool:
        
        @ContexaTool.register(
            name="web_search",
            description="Search the web and return text snippet"
        )
        async def web_search(inp: SearchInput) -> str:
            return f"Top hit for {inp.query}"
        """
        def decorator(func: Callable) -> ContexaTool:
            tool = cls(
                func=func,
                name=name,
                description=description,
                version=version,
            )
            from contexa_sdk.core.registry import register_tool
            register_tool(tool)
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await tool(*args, **kwargs)
                
            # Attach the tool to the function for retrieval
            wrapper.__contexa_tool__ = tool
            return wrapper
            
        return decorator


class RemoteTool(ContexaTool):
    """A tool that calls a remote MCP-compatible API."""
    
    endpoint_url: str
    
    def __init__(
        self,
        endpoint_url: str,
        name: str,
        description: str,
        version: str = "0.1.0",
        schema: Optional[Type[BaseModel]] = None,
        config: Optional[ContexaConfig] = None,
        tool_id: Optional[str] = None,
        **kwargs,
    ):
        """Initialize a RemoteTool.
        
        Args:
            endpoint_url: URL of the MCP-compatible API endpoint
            name: Name of the tool
            description: Description of the tool
            version: Version of the tool
            schema: Input schema for the tool
            config: Configuration for the tool
            tool_id: Unique ID for the tool (auto-generated if not provided)
        """
        async def remote_caller(**kwargs):
            """Call the remote MCP API."""
            import httpx
            
            client = httpx.AsyncClient(timeout=self.config.timeout)
            
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
                
            response = await client.post(
                self.endpoint_url,
                json=kwargs,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        
        super().__init__(
            func=remote_caller,
            name=name,
            description=description,
            version=version,
            schema=schema,
            config=config,
            tool_id=tool_id,
            **kwargs,
        )
        
        self.endpoint_url = endpoint_url 