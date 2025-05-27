"""
MCP Transport layer implementations.

This module provides different transport mechanisms for MCP communication,
including stdio, HTTP, and Server-Sent Events (SSE) transports as defined
in the MCP specification.
"""

import asyncio
import json
import sys
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable
import logging

from .protocol import MCPMessage, MCPProtocol

logger = logging.getLogger(__name__)


class MCPTransport(ABC):
    """Abstract base class for MCP transport implementations."""
    
    def __init__(self, protocol: MCPProtocol):
        self.protocol = protocol
        self.running = False
        self.message_handler: Optional[Callable[[Dict[str, Any]], Awaitable[Optional[MCPMessage]]]] = None
    
    @abstractmethod
    async def start(self):
        """Start the transport."""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the transport."""
        pass
    
    @abstractmethod
    async def send_message(self, message: MCPMessage):
        """Send a message through the transport."""
        pass
    
    def set_message_handler(self, handler: Callable[[Dict[str, Any]], Awaitable[Optional[MCPMessage]]]):
        """Set the message handler for incoming messages."""
        self.message_handler = handler


class StdioTransport(MCPTransport):
    """
    Standard input/output transport for MCP.
    
    This transport uses stdin/stdout for communication, which is ideal
    for local processes and simple integrations.
    """
    
    def __init__(self, protocol: MCPProtocol):
        super().__init__(protocol)
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._read_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the stdio transport."""
        if self.running:
            return
        
        logger.info("Starting stdio transport")
        
        # Set up stdin/stdout streams
        self.reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(self.reader)
        
        loop = asyncio.get_event_loop()
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        self.writer = asyncio.StreamWriter(
            transport=sys.stdout,
            protocol=asyncio.StreamReaderProtocol(asyncio.StreamReader()),
            reader=None,
            loop=loop
        )
        
        self.running = True
        
        # Start reading messages
        self._read_task = asyncio.create_task(self._read_messages())
        
        logger.info("Stdio transport started")
    
    async def stop(self):
        """Stop the stdio transport."""
        if not self.running:
            return
        
        logger.info("Stopping stdio transport")
        
        self.running = False
        
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        
        logger.info("Stdio transport stopped")
    
    async def send_message(self, message: MCPMessage):
        """Send a message through stdio."""
        if not self.running or not self.writer:
            raise RuntimeError("Transport not running")
        
        message_json = message.to_json()
        logger.debug(f"Sending message: {message_json}")
        
        self.writer.write(message_json.encode('utf-8') + b'\n')
        await self.writer.drain()
    
    async def _read_messages(self):
        """Read messages from stdin."""
        while self.running and self.reader:
            try:
                line = await self.reader.readline()
                if not line:
                    break
                
                line_str = line.decode('utf-8').strip()
                if not line_str:
                    continue
                
                logger.debug(f"Received message: {line_str}")
                
                # Parse JSON message
                try:
                    message_data = json.loads(line_str)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    continue
                
                # Handle message through protocol
                if self.message_handler:
                    response = await self.message_handler(message_data)
                    if response:
                        await self.send_message(response)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error reading message: {e}")


class HTTPTransport(MCPTransport):
    """
    HTTP transport for MCP using POST requests.
    
    This transport uses HTTP POST requests for client-to-server communication
    and can be combined with SSE for server-to-client communication.
    """
    
    def __init__(self, protocol: MCPProtocol, host: str = "0.0.0.0", port: int = 8000):
        super().__init__(protocol)
        self.host = host
        self.port = port
        self.app = None
        self.server = None
    
    async def start(self):
        """Start the HTTP transport."""
        if self.running:
            return
        
        logger.info(f"Starting HTTP transport on {self.host}:{self.port}")
        
        try:
            from fastapi import FastAPI, Request, HTTPException
            from fastapi.responses import JSONResponse
            import uvicorn
        except ImportError:
            raise RuntimeError("FastAPI and uvicorn are required for HTTP transport")
        
        self.app = FastAPI(title="MCP Server", description="Model Context Protocol Server")
        
        @self.app.post("/mcp")
        async def handle_mcp_request(request: Request):
            """Handle MCP requests via HTTP POST."""
            try:
                message_data = await request.json()
                
                if self.message_handler:
                    response = await self.message_handler(message_data)
                    if response:
                        return response.to_dict()
                    else:
                        return {"jsonrpc": "2.0", "result": None}
                else:
                    raise HTTPException(status_code=500, detail="No message handler configured")
                
            except Exception as e:
                logger.exception("Error handling HTTP request")
                return JSONResponse(
                    status_code=500,
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": "Internal error",
                            "data": str(e)
                        }
                    }
                )
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "ok", "transport": "http"}
        
        # Start the server
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        self.server = uvicorn.Server(config)
        
        self.running = True
        
        # Run server in background
        asyncio.create_task(self.server.serve())
        
        logger.info(f"HTTP transport started on http://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the HTTP transport."""
        if not self.running:
            return
        
        logger.info("Stopping HTTP transport")
        
        self.running = False
        
        if self.server:
            self.server.should_exit = True
        
        logger.info("HTTP transport stopped")
    
    async def send_message(self, message: MCPMessage):
        """Send a message through HTTP (not typically used for server-initiated messages)."""
        # HTTP transport typically doesn't send messages from server to client
        # This would be handled by SSE or webhooks
        logger.warning("HTTP transport cannot send server-initiated messages")


class SSETransport(MCPTransport):
    """
    Server-Sent Events transport for MCP.
    
    This transport uses SSE for server-to-client communication and can be
    combined with HTTP POST for client-to-server communication.
    """
    
    def __init__(self, protocol: MCPProtocol, host: str = "0.0.0.0", port: int = 8000):
        super().__init__(protocol)
        self.host = host
        self.port = port
        self.app = None
        self.server = None
        self.sse_connections = set()
    
    async def start(self):
        """Start the SSE transport."""
        if self.running:
            return
        
        logger.info(f"Starting SSE transport on {self.host}:{self.port}")
        
        try:
            from fastapi import FastAPI, Request, HTTPException
            from fastapi.responses import StreamingResponse
            from sse_starlette import EventSourceResponse
            import uvicorn
        except ImportError:
            raise RuntimeError("FastAPI, uvicorn, and sse-starlette are required for SSE transport")
        
        self.app = FastAPI(title="MCP SSE Server", description="Model Context Protocol SSE Server")
        
        @self.app.post("/mcp")
        async def handle_mcp_request(request: Request):
            """Handle MCP requests via HTTP POST."""
            try:
                message_data = await request.json()
                
                if self.message_handler:
                    response = await self.message_handler(message_data)
                    if response:
                        return response.to_dict()
                    else:
                        return {"jsonrpc": "2.0", "result": None}
                else:
                    raise HTTPException(status_code=500, detail="No message handler configured")
                
            except Exception as e:
                logger.exception("Error handling HTTP request")
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    }
                }
        
        @self.app.get("/mcp/events")
        async def sse_endpoint(request: Request):
            """SSE endpoint for server-to-client messages."""
            async def event_generator():
                connection_id = id(request)
                self.sse_connections.add(connection_id)
                
                try:
                    while True:
                        # Keep connection alive
                        yield {"data": json.dumps({"type": "ping", "timestamp": asyncio.get_event_loop().time()})}
                        await asyncio.sleep(30)  # Ping every 30 seconds
                        
                except asyncio.CancelledError:
                    pass
                finally:
                    self.sse_connections.discard(connection_id)
            
            return EventSourceResponse(event_generator())
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "ok", "transport": "sse", "connections": len(self.sse_connections)}
        
        # Start the server
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        self.server = uvicorn.Server(config)
        
        self.running = True
        
        # Run server in background
        asyncio.create_task(self.server.serve())
        
        logger.info(f"SSE transport started on http://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the SSE transport."""
        if not self.running:
            return
        
        logger.info("Stopping SSE transport")
        
        self.running = False
        
        if self.server:
            self.server.should_exit = True
        
        # Close all SSE connections
        self.sse_connections.clear()
        
        logger.info("SSE transport stopped")
    
    async def send_message(self, message: MCPMessage):
        """Send a message through SSE to all connected clients."""
        if not self.running:
            raise RuntimeError("Transport not running")
        
        message_json = message.to_json()
        logger.debug(f"Broadcasting SSE message: {message_json}")
        
        # In a real implementation, we would send this to all SSE connections
        # For now, we just log it
        logger.info(f"Would broadcast to {len(self.sse_connections)} SSE connections")


def create_transport(
    transport_type: str,
    protocol: MCPProtocol,
    **kwargs
) -> MCPTransport:
    """
    Create a transport instance based on type.
    
    Args:
        transport_type: Type of transport ("stdio", "http", "sse")
        protocol: MCP protocol instance
        **kwargs: Additional arguments for transport
        
    Returns:
        MCPTransport instance
    """
    if transport_type == "stdio":
        return StdioTransport(protocol)
    elif transport_type == "http":
        return HTTPTransport(protocol, **kwargs)
    elif transport_type == "sse":
        return SSETransport(protocol, **kwargs)
    else:
        raise ValueError(f"Unknown transport type: {transport_type}") 