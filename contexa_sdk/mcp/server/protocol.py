"""
MCP Protocol implementation following JSON-RPC 2.0 specification.

This module implements the core Model Context Protocol message handling,
including request/response patterns, notifications, and error handling
as defined in the MCP specification.
"""

import json
import uuid
import asyncio
from typing import Dict, Any, Optional, Union, Callable, Awaitable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MCPErrorCode(Enum):
    """Standard MCP error codes based on JSON-RPC 2.0."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP-specific error codes
    CAPABILITY_NOT_SUPPORTED = -32000
    RESOURCE_NOT_FOUND = -32001
    TOOL_EXECUTION_ERROR = -32002
    AUTHENTICATION_REQUIRED = -32003
    PERMISSION_DENIED = -32004
    RATE_LIMITED = -32005


@dataclass
class MCPMessage:
    """Base class for all MCP messages."""
    jsonrpc: str = "2.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Create message from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MCPMessage':
        """Create message from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class MCPRequest(MCPMessage):
    """MCP request message."""
    method: str = None
    id: Union[str, int] = None
    params: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        super().__post_init__() if hasattr(super(), '__post_init__') else None
        if self.id is None:
            self.id = str(uuid.uuid4())


@dataclass
class MCPResponse(MCPMessage):
    """MCP response message."""
    id: Union[str, int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    
    def is_error(self) -> bool:
        """Check if this is an error response."""
        return self.error is not None


@dataclass
class MCPNotification(MCPMessage):
    """MCP notification message (no response expected)."""
    method: str = None
    params: Optional[Dict[str, Any]] = None


@dataclass
class MCPError:
    """MCP error object."""
    code: int
    message: str
    data: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result


class MCPProtocol:
    """
    Core MCP protocol implementation.
    
    Handles JSON-RPC 2.0 message parsing, routing, and response generation
    according to the MCP specification.
    """
    
    def __init__(self):
        self.request_handlers: Dict[str, Callable] = {}
        self.notification_handlers: Dict[str, Callable] = {}
        self.pending_requests: Dict[Union[str, int], asyncio.Future] = {}
        self.initialized = False
        
    def register_request_handler(
        self, 
        method: str, 
        handler: Callable[[MCPRequest], Awaitable[Dict[str, Any]]]
    ):
        """Register a handler for a specific request method."""
        self.request_handlers[method] = handler
        logger.debug(f"Registered request handler for method: {method}")
    
    def register_notification_handler(
        self, 
        method: str, 
        handler: Callable[[MCPNotification], Awaitable[None]]
    ):
        """Register a handler for a specific notification method."""
        self.notification_handlers[method] = handler
        logger.debug(f"Registered notification handler for method: {method}")
    
    async def handle_message(self, message_data: Dict[str, Any]) -> Optional[MCPResponse]:
        """
        Handle an incoming MCP message.
        
        Args:
            message_data: Parsed JSON message data
            
        Returns:
            MCPResponse if the message was a request, None for notifications
        """
        try:
            # Validate JSON-RPC version
            if message_data.get("jsonrpc") != "2.0":
                return self._create_error_response(
                    None, MCPErrorCode.INVALID_REQUEST, "Invalid JSON-RPC version"
                )
            
            # Determine message type
            if "id" in message_data and "method" in message_data:
                # Request
                request = MCPRequest.from_dict(message_data)
                return await self._handle_request(request)
            elif "method" in message_data and "id" not in message_data:
                # Notification
                notification = MCPNotification.from_dict(message_data)
                await self._handle_notification(notification)
                return None
            elif "id" in message_data and ("result" in message_data or "error" in message_data):
                # Response
                response = MCPResponse.from_dict(message_data)
                await self._handle_response(response)
                return None
            else:
                return self._create_error_response(
                    None, MCPErrorCode.INVALID_REQUEST, "Invalid message format"
                )
                
        except json.JSONDecodeError:
            return self._create_error_response(
                None, MCPErrorCode.PARSE_ERROR, "Invalid JSON"
            )
        except Exception as e:
            logger.exception("Error handling message")
            return self._create_error_response(
                None, MCPErrorCode.INTERNAL_ERROR, str(e)
            )
    
    async def _handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle an incoming request."""
        try:
            # Check if method is supported
            if request.method not in self.request_handlers:
                return self._create_error_response(
                    request.id, MCPErrorCode.METHOD_NOT_FOUND, 
                    f"Method '{request.method}' not found"
                )
            
            # Call the handler
            handler = self.request_handlers[request.method]
            result = await handler(request)
            
            return MCPResponse(id=request.id, result=result)
            
        except Exception as e:
            logger.exception(f"Error handling request {request.method}")
            return self._create_error_response(
                request.id, MCPErrorCode.INTERNAL_ERROR, str(e)
            )
    
    async def _handle_notification(self, notification: MCPNotification):
        """Handle an incoming notification."""
        try:
            if notification.method in self.notification_handlers:
                handler = self.notification_handlers[notification.method]
                await handler(notification)
            else:
                logger.warning(f"No handler for notification method: {notification.method}")
                
        except Exception as e:
            logger.exception(f"Error handling notification {notification.method}")
    
    async def _handle_response(self, response: MCPResponse):
        """Handle an incoming response to a previous request."""
        if response.id in self.pending_requests:
            future = self.pending_requests.pop(response.id)
            if not future.done():
                future.set_result(response)
    
    def _create_error_response(
        self, 
        request_id: Optional[Union[str, int]], 
        error_code: MCPErrorCode, 
        message: str,
        data: Optional[Any] = None
    ) -> MCPResponse:
        """Create an error response."""
        error = MCPError(code=error_code.value, message=message, data=data)
        return MCPResponse(id=request_id, error=error.to_dict())
    
    async def send_request(
        self, 
        method: str, 
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> MCPResponse:
        """
        Send a request and wait for response.
        
        Args:
            method: Request method name
            params: Request parameters
            timeout: Timeout in seconds
            
        Returns:
            MCPResponse object
        """
        request = MCPRequest(method=method, params=params, id=str(uuid.uuid4()))
        
        # Create future for response
        future = asyncio.Future()
        self.pending_requests[request.id] = future
        
        try:
            # Send request (implementation depends on transport)
            await self._send_message(request)
            
            # Wait for response
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
            
        except asyncio.TimeoutError:
            self.pending_requests.pop(request.id, None)
            raise
        except Exception:
            self.pending_requests.pop(request.id, None)
            raise
    
    async def send_notification(
        self, 
        method: str, 
        params: Optional[Dict[str, Any]] = None
    ):
        """Send a notification (no response expected)."""
        notification = MCPNotification(method=method, params=params)
        await self._send_message(notification)
    
    async def _send_message(self, message: MCPMessage):
        """Send a message (to be implemented by transport layer)."""
        raise NotImplementedError("Transport layer must implement _send_message")
    
    def create_initialize_request(
        self, 
        protocol_version: str = "2025-03-26",
        capabilities: Optional[Dict[str, Any]] = None,
        client_info: Optional[Dict[str, Any]] = None
    ) -> MCPRequest:
        """Create an initialization request."""
        params = {
            "protocolVersion": protocol_version,
            "capabilities": capabilities or {},
        }
        if client_info:
            params["clientInfo"] = client_info
            
        return MCPRequest(method="initialize", params=params, id=str(uuid.uuid4()))
    
    def create_initialized_notification(self) -> MCPNotification:
        """Create an initialized notification."""
        return MCPNotification(method="initialized") 