"""
Model Context Protocol (MCP) integration for Contexa SDK.

This package provides integration with the Model Context Protocol,
enabling Contexa agents to be exposed as MCP-compatible services
and to consume remote MCP services.
"""

__all__ = [
    'client',
    'server',
    'expose_as_mcp',
    'invoke_mcp_service',
]

# Helper function for exposing an agent as an MCP endpoint
def expose_as_mcp(agent_or_team, endpoint=None, host="0.0.0.0", port=3000):
    """
    Expose a Contexa agent or team as an MCP-compatible endpoint.
    
    Args:
        agent_or_team: The Contexa agent or team to expose
        endpoint: Optional endpoint path (defaults to /{agent_name})
        host: Host to bind server to
        port: Port to bind server to
        
    Returns:
        An MCP endpoint object that can be started with .run()
    """
    from contexa_sdk.mcp.server import MCPServer
    server = MCPServer(host=host, port=port)
    server.register(agent_or_team, endpoint)
    return server

# Helper function for invoking an MCP service
def invoke_mcp_service(url, input_data, auth=None):
    """
    Invoke a remote MCP-compatible service.
    
    Args:
        url: The URL of the MCP service
        input_data: The input data to send
        auth: Optional authentication information
        
    Returns:
        The response from the MCP service
    """
    from contexa_sdk.mcp.client import MCPClient
    client = MCPClient()
    return client.invoke(url, input_data, auth=auth) 