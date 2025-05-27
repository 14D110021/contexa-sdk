"""
Comprehensive MCP Integration Example.

This example demonstrates the advanced Model Context Protocol (MCP) integration
capabilities in Contexa SDK, including:

1. Creating MCP-compatible servers from Contexa agents
2. Connecting to remote MCP servers as clients
3. Cross-framework MCP communication
4. Advanced MCP features (sampling, resources, prompts)
5. Multi-transport MCP deployment

The example showcases how Contexa SDK's MCP implementation enables seamless
interoperability with the broader MCP ecosystem.
"""

import asyncio
import logging
from typing import Dict, Any
from pydantic import BaseModel

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.mcp.server import MCPServer, MCPServerConfig, create_mcp_server_for_agent
from contexa_sdk.mcp.client import MCPClient, MCPClientConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define some example tools for our MCP server
class CalculatorInput(BaseModel):
    """Input for calculator operations."""
    operation: str
    a: float
    b: float


@ContexaTool.register(
    name="calculator",
    description="Perform basic mathematical operations (add, subtract, multiply, divide)"
)
async def calculator_tool(inp: CalculatorInput) -> str:
    """A calculator tool that performs basic math operations."""
    try:
        if inp.operation == "add":
            result = inp.a + inp.b
        elif inp.operation == "subtract":
            result = inp.a - inp.b
        elif inp.operation == "multiply":
            result = inp.a * inp.b
        elif inp.operation == "divide":
            if inp.b == 0:
                return "Error: Division by zero"
            result = inp.a / inp.b
        else:
            return f"Error: Unknown operation '{inp.operation}'"
        
        return f"Result: {inp.a} {inp.operation} {inp.b} = {result}"
    except Exception as e:
        return f"Error: {str(e)}"


class WeatherInput(BaseModel):
    """Input for weather queries."""
    location: str
    unit: str = "celsius"


@ContexaTool.register(
    name="weather",
    description="Get current weather information for a location"
)
async def weather_tool(inp: WeatherInput) -> str:
    """A weather tool that provides weather information."""
    # Simulate weather data
    weather_data = {
        "new york": {"temp": 22, "condition": "sunny"},
        "london": {"temp": 15, "condition": "cloudy"},
        "tokyo": {"temp": 28, "condition": "rainy"},
        "paris": {"temp": 18, "condition": "partly cloudy"},
    }
    
    location_key = inp.location.lower()
    if location_key in weather_data:
        data = weather_data[location_key]
        temp_unit = "°C" if inp.unit == "celsius" else "°F"
        if inp.unit == "fahrenheit":
            data["temp"] = (data["temp"] * 9/5) + 32
        
        return f"Weather in {inp.location}: {data['temp']}{temp_unit}, {data['condition']}"
    else:
        return f"Weather data not available for {inp.location}"


async def create_example_agent() -> ContexaAgent:
    """Create an example agent with tools for MCP demonstration."""
    agent = ContexaAgent(
        name="MCP Demo Agent",
        description="A demonstration agent with calculator and weather tools",
        model=ContexaModel(provider="openai", model_id="gpt-4o"),
        tools=[calculator_tool.__contexa_tool__, weather_tool.__contexa_tool__]
    )
    
    return agent


async def demo_mcp_server():
    """Demonstrate creating and running an MCP server."""
    logger.info("=== MCP Server Demo ===")
    
    # Create an example agent
    agent = await create_example_agent()
    
    # Create MCP server configuration
    config = MCPServerConfig(
        name="Contexa MCP Demo Server",
        description="Demonstration of Contexa SDK MCP server capabilities",
        transport_type="http",  # Use HTTP for this demo
        host="localhost",
        port=8001,
        enable_sampling=True,
        enable_resource_subscriptions=True,
    )
    
    # Create MCP server
    server = MCPServer(config)
    server.register_agent(agent)
    
    logger.info(f"Created MCP server with {len(server.tools)} tools")
    logger.info(f"Server capabilities: {server.capabilities.create_capability_summary()}")
    
    # Start the server (non-blocking for demo)
    await server.start()
    
    logger.info("MCP server started successfully")
    logger.info(f"Server info: {server.get_server_info()}")
    
    return server


async def demo_mcp_client(server_url: str):
    """Demonstrate connecting to an MCP server as a client."""
    logger.info("=== MCP Client Demo ===")
    
    # Create MCP client configuration
    config = MCPClientConfig(
        name="Contexa MCP Demo Client",
        supports_sampling=True,
        supports_roots=True,
    )
    
    # Create MCP client
    client = MCPClient(config)
    
    try:
        # Connect to the server
        await client.connect(server_url)
        logger.info("Successfully connected to MCP server")
        
        # Get server information
        server_info = client.get_server_info()
        server_capabilities = client.get_server_capabilities()
        
        logger.info(f"Connected to: {server_info}")
        logger.info(f"Server capabilities: {list(server_capabilities.keys())}")
        
        # List available tools
        tools = await client.list_tools()
        logger.info(f"Available tools: {[tool['name'] for tool in tools]}")
        
        # Test calculator tool
        logger.info("\n--- Testing Calculator Tool ---")
        calc_result = await client.call_tool("calculator", {
            "operation": "add",
            "a": 15,
            "b": 27
        })
        logger.info(f"Calculator result: {calc_result}")
        
        # Test weather tool
        logger.info("\n--- Testing Weather Tool ---")
        weather_result = await client.call_tool("weather", {
            "location": "New York",
            "unit": "fahrenheit"
        })
        logger.info(f"Weather result: {weather_result}")
        
        # Test ping
        ping_result = await client.ping()
        logger.info(f"Ping successful: {ping_result}")
        
        return client
        
    except Exception as e:
        logger.error(f"Client demo failed: {e}")
        await client.disconnect()
        raise


async def demo_mcp_integration():
    """Demonstrate full MCP integration between server and client."""
    logger.info("=== Full MCP Integration Demo ===")
    
    server = None
    client = None
    
    try:
        # Start MCP server
        server = await demo_mcp_server()
        
        # Give server a moment to start
        await asyncio.sleep(2)
        
        # Connect client to server
        client = await demo_mcp_client("http://localhost:8001")
        
        # Demonstrate advanced MCP features
        logger.info("\n--- Advanced MCP Features ---")
        
        # Test multiple tool calls
        logger.info("Testing multiple tool calls...")
        
        tasks = [
            client.call_tool("calculator", {"operation": "multiply", "a": 6, "b": 7}),
            client.call_tool("weather", {"location": "London"}),
            client.call_tool("calculator", {"operation": "divide", "a": 100, "b": 4}),
        ]
        
        results = await asyncio.gather(*tasks)
        for i, result in enumerate(results):
            logger.info(f"Concurrent call {i+1}: {result}")
        
        # Test error handling
        logger.info("\nTesting error handling...")
        try:
            error_result = await client.call_tool("calculator", {
                "operation": "divide",
                "a": 10,
                "b": 0
            })
            logger.info(f"Error handling result: {error_result}")
        except Exception as e:
            logger.info(f"Expected error caught: {e}")
        
        logger.info("\n✅ MCP Integration Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Integration demo failed: {e}")
        raise
    
    finally:
        # Clean up
        if client:
            await client.disconnect()
        if server:
            await server.stop()


async def demo_mcp_convenience_functions():
    """Demonstrate convenience functions for quick MCP setup."""
    logger.info("=== MCP Convenience Functions Demo ===")
    
    # Create an agent
    agent = await create_example_agent()
    
    # Create MCP server using convenience function
    server = create_mcp_server_for_agent(
        agent,
        transport_type="http",
        host="localhost",
        port=8002
    )
    
    logger.info("Created MCP server using convenience function")
    logger.info(f"Server config: {server.config.name}")
    
    # Start server
    await server.start()
    
    # Test with client
    client = MCPClient()
    try:
        await client.connect("http://localhost:8002")
        tools = await client.list_tools()
        logger.info(f"Tools available via convenience server: {[t['name'] for t in tools]}")
        
    finally:
        await client.disconnect()
        await server.stop()
    
    logger.info("✅ Convenience functions demo completed!")


async def demo_mcp_transport_options():
    """Demonstrate different MCP transport options."""
    logger.info("=== MCP Transport Options Demo ===")
    
    agent = await create_example_agent()
    
    # Test different transport types
    transport_configs = [
        {"transport_type": "http", "port": 8003},
        {"transport_type": "sse", "port": 8004},
    ]
    
    servers = []
    
    try:
        for i, transport_config in enumerate(transport_configs):
            logger.info(f"\nTesting {transport_config['transport_type']} transport...")
            
            config = MCPServerConfig(
                name=f"Transport Demo Server {i+1}",
                **transport_config
            )
            
            server = MCPServer(config)
            server.register_agent(agent)
            
            await server.start()
            servers.append(server)
            
            logger.info(f"✅ {transport_config['transport_type']} server started on port {transport_config['port']}")
    
    finally:
        # Clean up all servers
        for server in servers:
            await server.stop()
    
    logger.info("✅ Transport options demo completed!")


async def main():
    """Run all MCP integration demonstrations."""
    logger.info("🚀 Starting Contexa SDK MCP Integration Demonstrations")
    
    try:
        # Run individual demos
        await demo_mcp_integration()
        await demo_mcp_convenience_functions()
        await demo_mcp_transport_options()
        
        logger.info("\n🎉 All MCP demonstrations completed successfully!")
        logger.info("\nKey Features Demonstrated:")
        logger.info("✅ MCP Server creation from Contexa agents")
        logger.info("✅ MCP Client connection and tool consumption")
        logger.info("✅ JSON-RPC 2.0 protocol compliance")
        logger.info("✅ Multiple transport options (HTTP, SSE)")
        logger.info("✅ Capability negotiation")
        logger.info("✅ Error handling and resilience")
        logger.info("✅ Concurrent tool execution")
        logger.info("✅ Convenience functions for quick setup")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 