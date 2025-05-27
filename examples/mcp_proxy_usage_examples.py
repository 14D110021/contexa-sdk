"""
MCP Proxy Usage Examples for Contexa SDK

This module demonstrates comprehensive usage of MCP client proxies for transparent
remote capability access. These examples show real-world scenarios and best practices
for using the MCP proxy system in distributed agent architectures.

Examples included:
1. Basic proxy usage with single server
2. Multi-server load balancing and failover
3. Advanced caching strategies
4. Integration with existing Contexa agents
5. Error handling and recovery patterns
6. Performance optimization techniques
"""

import asyncio
import logging
from typing import Dict, Any, List
from contexa_sdk.mcp.client.proxy import (
    MCPProxyConfig, MCPToolProxy, MCPResourceProxy, MCPPromptProxy
)
from contexa_sdk.mcp.client.proxy_factory import (
    MCPProxyFactory, MCPProxyManager, create_mcp_proxy_factory
)
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_1_basic_proxy_usage():
    """
    Example 1: Basic MCP Proxy Usage
    
    Demonstrates how to create and use MCP proxies for accessing remote
    tools, resources, and prompts from a single MCP server.
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic MCP Proxy Usage")
    print("="*60)
    
    # Configure connection to MCP server
    config = MCPProxyConfig(
        server_url="http://localhost:8000",
        timeout=30.0,
        cache_ttl=300,  # 5 minutes
        enable_caching=True
    )
    
    try:
        # Create proxy factory
        async with create_mcp_proxy_factory(config) as factory:
            print("✅ Connected to MCP server")
            
            # 1. Create a tool proxy for remote calculator
            calculator_proxy = await factory.create_tool_proxy("calculator")
            print("📊 Created calculator tool proxy")
            
            # Use the remote tool as if it were local
            result = await calculator_proxy.execute({
                "operation": "add",
                "a": 15,
                "b": 27
            })
            print(f"🧮 Calculator result: {result}")
            
            # 2. Create a resource proxy for accessing remote files
            resource_proxy = await factory.create_resource_proxy()
            print("📁 Created resource proxy")
            
            # List available resources
            resources = await resource_proxy.list_resources()
            print(f"📋 Found {len(resources)} resources:")
            for resource in resources[:3]:  # Show first 3
                print(f"   - {resource.name}: {resource.uri}")
            
            # Read a specific resource
            if resources:
                content = await resource_proxy.read_resource(resources[0].uri)
                print(f"📄 Resource content preview: {str(content)[:100]}...")
            
            # 3. Create a prompt proxy for remote templates
            prompt_proxy = await factory.create_prompt_proxy()
            print("💬 Created prompt proxy")
            
            # List available prompt templates
            templates = await prompt_proxy.list_prompts()
            print(f"📝 Found {len(templates)} prompt templates:")
            for template in templates[:3]:  # Show first 3
                print(f"   - {template.name}: {template.description}")
            
            # Execute a prompt template
            if templates:
                prompt_result = await prompt_proxy.get_prompt(
                    templates[0].name,
                    arguments={"text": "Hello, world! This is a test."}
                )
                print(f"💭 Prompt result: {prompt_result}")
            
            print("✅ Basic proxy usage completed successfully")
            
    except Exception as e:
        print(f"❌ Error in basic proxy usage: {e}")


async def example_2_multi_server_load_balancing():
    """
    Example 2: Multi-Server Load Balancing and Failover
    
    Demonstrates how to use MCPProxyManager for load balancing across
    multiple MCP servers with automatic failover capabilities.
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Multi-Server Load Balancing")
    print("="*60)
    
    # Configure multiple server endpoints
    server_configs = [
        MCPProxyConfig(server_url="http://server1:8000", timeout=10.0),
        MCPProxyConfig(server_url="http://server2:8000", timeout=10.0),
        MCPProxyConfig(server_url="http://server3:8000", timeout=10.0),
    ]
    
    try:
        # Create proxy manager for load balancing
        manager = MCPProxyManager(server_configs)
        print("🔄 Created proxy manager with 3 servers")
        
        # Get factory with automatic load balancing
        factory1 = await manager.get_factory()  # Will select healthy server
        print("🎯 Got factory from load balancer")
        
        # Create tool proxy through load-balanced factory
        tool_proxy = await factory1.create_tool_proxy("data_processor")
        print("⚙️ Created data processor tool proxy")
        
        # Simulate multiple requests with load balancing
        for i in range(5):
            try:
                # Each request may go to a different server
                factory = await manager.get_factory()
                proxy = await factory.create_tool_proxy("load_test_tool")
                
                result = await proxy.execute({"request_id": i, "data": f"test_data_{i}"})
                print(f"📊 Request {i+1} result: {result}")
                
            except Exception as e:
                print(f"⚠️ Request {i+1} failed, trying next server: {e}")
        
        # Demonstrate specific server selection
        try:
            specific_factory = await manager.get_factory("http://server2:8000")
            specific_proxy = await specific_factory.create_tool_proxy("server2_tool")
            print("🎯 Created proxy for specific server")
        except Exception as e:
            print(f"⚠️ Specific server unavailable: {e}")
        
        # Cleanup
        await manager.close()
        print("✅ Multi-server load balancing completed")
        
    except Exception as e:
        print(f"❌ Error in load balancing example: {e}")


async def example_3_advanced_caching_strategies():
    """
    Example 3: Advanced Caching Strategies
    
    Demonstrates different caching configurations and strategies for
    optimizing performance in various scenarios.
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Advanced Caching Strategies")
    print("="*60)
    
    try:
        # Configuration for high-performance caching
        high_perf_config = MCPProxyConfig(
            server_url="http://localhost:8000",
            cache_ttl=600,      # 10 minutes
            cache_size=500,     # Large cache
            enable_caching=True
        )
        
        # Configuration for low-latency scenarios
        low_latency_config = MCPProxyConfig(
            server_url="http://localhost:8000",
            cache_ttl=60,       # 1 minute
            cache_size=50,      # Small cache
            enable_caching=True
        )
        
        # Configuration for real-time scenarios (no caching)
        realtime_config = MCPProxyConfig(
            server_url="http://localhost:8000",
            enable_caching=False  # No caching for real-time data
        )
        
        # Demonstrate high-performance caching
        async with create_mcp_proxy_factory(high_perf_config) as hp_factory:
            print("🚀 Testing high-performance caching")
            
            tool_proxy = await hp_factory.create_tool_proxy("expensive_computation")
            
            # First call - will cache result
            start_time = asyncio.get_event_loop().time()
            result1 = await tool_proxy.execute({"input": "complex_data"})
            first_call_time = asyncio.get_event_loop().time() - start_time
            print(f"⏱️ First call (cached): {first_call_time:.3f}s")
            
            # Second call - should use cache
            start_time = asyncio.get_event_loop().time()
            result2 = await tool_proxy.execute({"input": "complex_data"})
            second_call_time = asyncio.get_event_loop().time() - start_time
            print(f"⚡ Second call (from cache): {second_call_time:.3f}s")
            
            print(f"🎯 Cache speedup: {first_call_time/second_call_time:.1f}x faster")
        
        # Demonstrate cache management
        async with create_mcp_proxy_factory(low_latency_config) as ll_factory:
            print("\n🔧 Testing cache management")
            
            resource_proxy = await ll_factory.create_resource_proxy()
            
            # Load resources into cache
            resources = await resource_proxy.list_resources()
            print(f"📚 Loaded {len(resources)} resources into cache")
            
            # Clear cache manually
            resource_proxy.clear_cache()
            print("🧹 Cache cleared manually")
            
            # Reload resources
            resources = await resource_proxy.list_resources(refresh_cache=True)
            print(f"🔄 Reloaded {len(resources)} resources")
        
        print("✅ Advanced caching strategies completed")
        
    except Exception as e:
        print(f"❌ Error in caching example: {e}")


async def example_4_agent_integration():
    """
    Example 4: Integration with Existing Contexa Agents
    
    Demonstrates how to integrate MCP proxies with existing Contexa agents
    to enable hybrid local/remote agent architectures.
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Agent Integration")
    print("="*60)
    
    try:
        # Create a local Contexa agent
        local_agent = ContexaAgent(
            name="HybridAgent",
            description="Agent that uses both local and remote tools",
            model=ContexaModel(provider="openai", model_id="gpt-4o"),
            tools=[]  # Will add tools dynamically
        )
        print("🤖 Created local Contexa agent")
        
        # Configure MCP proxy
        config = MCPProxyConfig(server_url="http://localhost:8000")
        
        async with create_mcp_proxy_factory(config) as factory:
            # Create remote tool proxies
            calculator_proxy = await factory.create_tool_proxy("calculator")
            weather_proxy = await factory.create_tool_proxy("weather_service")
            print("🔧 Created remote tool proxies")
            
            # Add remote tools to local agent
            # Note: In a real implementation, you'd register these with the agent
            remote_tools = [calculator_proxy, weather_proxy]
            
            # Simulate agent workflow using both local and remote capabilities
            print("\n🔄 Executing hybrid agent workflow:")
            
            # Step 1: Use remote calculator
            calc_result = await calculator_proxy.execute({
                "operation": "multiply",
                "a": 25,
                "b": 4
            })
            print(f"🧮 Remote calculation: 25 × 4 = {calc_result}")
            
            # Step 2: Use remote weather service
            weather_result = await weather_proxy.execute({
                "location": "San Francisco",
                "units": "celsius"
            })
            print(f"🌤️ Remote weather: {weather_result}")
            
            # Step 3: Create resource proxy for agent memory
            resource_proxy = await factory.create_resource_proxy()
            
            # Subscribe to agent state updates
            await resource_proxy.subscribe_to_resource("agent://state/memory")
            print("📡 Subscribed to agent state updates")
            
            # Step 4: Use prompt proxy for dynamic prompts
            prompt_proxy = await factory.create_prompt_proxy()
            
            dynamic_prompt = await prompt_proxy.get_prompt(
                "agent_instruction",
                arguments={
                    "task": "weather analysis",
                    "context": f"calculation result: {calc_result}, weather: {weather_result}"
                }
            )
            print(f"💭 Dynamic prompt generated: {dynamic_prompt}")
            
            print("✅ Agent integration completed successfully")
            
    except Exception as e:
        print(f"❌ Error in agent integration: {e}")


async def example_5_error_handling_patterns():
    """
    Example 5: Error Handling and Recovery Patterns
    
    Demonstrates robust error handling and recovery strategies for
    distributed MCP proxy scenarios.
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Error Handling and Recovery")
    print("="*60)
    
    try:
        # Configuration with aggressive timeouts for testing
        config = MCPProxyConfig(
            server_url="http://unreliable-server:8000",
            timeout=5.0,
            max_retries=3,
            retry_delay=1.0
        )
        
        async with create_mcp_proxy_factory(config) as factory:
            print("🔧 Testing error handling patterns")
            
            # Test 1: Handle connection failures gracefully
            try:
                tool_proxy = await factory.create_tool_proxy("unreliable_tool")
                result = await tool_proxy.execute({"test": "connection_failure"})
                print(f"✅ Unexpected success: {result}")
            except Exception as e:
                print(f"🔄 Handled connection failure: {type(e).__name__}")
            
            # Test 2: Implement circuit breaker pattern
            failure_count = 0
            max_failures = 3
            
            for attempt in range(5):
                try:
                    if failure_count >= max_failures:
                        print("🚫 Circuit breaker: Too many failures, skipping request")
                        await asyncio.sleep(2)  # Wait before retry
                        failure_count = 0  # Reset after wait
                        continue
                    
                    # Simulate tool execution
                    tool_proxy = await factory.create_tool_proxy(f"test_tool_{attempt}")
                    result = await tool_proxy.execute({"attempt": attempt})
                    print(f"✅ Attempt {attempt + 1} succeeded")
                    failure_count = 0  # Reset on success
                    
                except Exception as e:
                    failure_count += 1
                    print(f"❌ Attempt {attempt + 1} failed ({failure_count}/{max_failures}): {type(e).__name__}")
            
            # Test 3: Graceful degradation
            print("\n🔄 Testing graceful degradation")
            
            try:
                # Try primary service
                primary_proxy = await factory.create_tool_proxy("primary_service")
                result = await primary_proxy.execute({"service": "primary"})
                print(f"✅ Primary service: {result}")
            except Exception:
                try:
                    # Fallback to secondary service
                    secondary_proxy = await factory.create_tool_proxy("secondary_service")
                    result = await secondary_proxy.execute({"service": "secondary"})
                    print(f"🔄 Secondary service: {result}")
                except Exception:
                    # Final fallback to local processing
                    result = "local_fallback_result"
                    print(f"🏠 Local fallback: {result}")
            
            print("✅ Error handling patterns completed")
            
    except Exception as e:
        print(f"❌ Error in error handling example: {e}")


async def example_6_performance_optimization():
    """
    Example 6: Performance Optimization Techniques
    
    Demonstrates various techniques for optimizing MCP proxy performance
    including connection pooling, batch operations, and async patterns.
    """
    print("\n" + "="*60)
    print("EXAMPLE 6: Performance Optimization")
    print("="*60)
    
    try:
        # High-performance configuration
        config = MCPProxyConfig(
            server_url="http://localhost:8000",
            connection_pool_size=20,  # Large connection pool
            cache_size=1000,          # Large cache
            cache_ttl=300,            # 5-minute cache
            timeout=30.0
        )
        
        async with create_mcp_proxy_factory(config) as factory:
            print("🚀 Testing performance optimization techniques")
            
            # Technique 1: Concurrent tool execution
            print("\n⚡ Concurrent tool execution:")
            
            start_time = asyncio.get_event_loop().time()
            
            # Create multiple tool proxies
            tool_proxies = []
            for i in range(5):
                proxy = await factory.create_tool_proxy(f"parallel_tool_{i}")
                tool_proxies.append(proxy)
            
            # Execute tools concurrently
            tasks = []
            for i, proxy in enumerate(tool_proxies):
                task = proxy.execute({"task_id": i, "data": f"parallel_data_{i}"})
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            concurrent_time = asyncio.get_event_loop().time() - start_time
            print(f"⏱️ Concurrent execution: {concurrent_time:.3f}s for {len(tasks)} tasks")
            
            # Technique 2: Batch resource loading
            print("\n📦 Batch resource loading:")
            
            resource_proxy = await factory.create_resource_proxy()
            
            start_time = asyncio.get_event_loop().time()
            
            # Load multiple resources concurrently
            resources = await resource_proxy.list_resources()
            if len(resources) >= 3:
                batch_tasks = []
                for resource in resources[:3]:
                    task = resource_proxy.read_resource(resource.uri)
                    batch_tasks.append(task)
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                batch_time = asyncio.get_event_loop().time() - start_time
                print(f"📊 Batch loading: {batch_time:.3f}s for {len(batch_tasks)} resources")
            
            # Technique 3: Connection reuse demonstration
            print("\n🔄 Connection reuse:")
            
            # Multiple operations using the same factory (connection reuse)
            start_time = asyncio.get_event_loop().time()
            
            for i in range(10):
                proxy = await factory.get_tool_proxy("reuse_test_tool") or \
                        await factory.create_tool_proxy("reuse_test_tool")
                # Simulate quick operation
                await asyncio.sleep(0.01)  # Simulate work
            
            reuse_time = asyncio.get_event_loop().time() - start_time
            print(f"🔗 Connection reuse: {reuse_time:.3f}s for 10 operations")
            
            # Technique 4: Cache warming
            print("\n🔥 Cache warming:")
            
            start_time = asyncio.get_event_loop().time()
            
            # Pre-warm caches with common operations
            warming_tasks = []
            for i in range(5):
                proxy = await factory.create_tool_proxy(f"common_tool_{i}")
                task = proxy.execute({"warm_cache": True, "tool_id": i})
                warming_tasks.append(task)
            
            await asyncio.gather(*warming_tasks, return_exceptions=True)
            
            warming_time = asyncio.get_event_loop().time() - start_time
            print(f"🔥 Cache warming: {warming_time:.3f}s")
            
            # Now subsequent calls should be faster
            start_time = asyncio.get_event_loop().time()
            
            cached_tasks = []
            for i in range(5):
                proxy = await factory.get_tool_proxy(f"common_tool_{i}")
                if proxy:
                    task = proxy.execute({"use_cache": True, "tool_id": i})
                    cached_tasks.append(task)
            
            if cached_tasks:
                await asyncio.gather(*cached_tasks, return_exceptions=True)
                cached_time = asyncio.get_event_loop().time() - start_time
                print(f"⚡ Cached execution: {cached_time:.3f}s (speedup: {warming_time/cached_time:.1f}x)")
            
            print("✅ Performance optimization completed")
            
    except Exception as e:
        print(f"❌ Error in performance optimization: {e}")


async def main():
    """
    Main function to run all MCP proxy usage examples.
    
    This demonstrates the complete range of MCP proxy capabilities
    and best practices for real-world usage.
    """
    print("🚀 MCP Proxy Usage Examples for Contexa SDK")
    print("=" * 80)
    print("Demonstrating transparent remote capability access with MCP proxies")
    print("=" * 80)
    
    examples = [
        ("Basic Proxy Usage", example_1_basic_proxy_usage),
        ("Multi-Server Load Balancing", example_2_multi_server_load_balancing),
        ("Advanced Caching Strategies", example_3_advanced_caching_strategies),
        ("Agent Integration", example_4_agent_integration),
        ("Error Handling Patterns", example_5_error_handling_patterns),
        ("Performance Optimization", example_6_performance_optimization),
    ]
    
    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n❌ Example '{name}' failed: {e}")
            logger.exception(f"Error in example: {name}")
        
        print("\n" + "-" * 60)
        await asyncio.sleep(0.5)  # Brief pause between examples
    
    print("\n🎉 All MCP proxy examples completed!")
    print("\nKey Takeaways:")
    print("✅ MCP proxies provide transparent remote capability access")
    print("✅ Load balancing and failover ensure high availability")
    print("✅ Intelligent caching optimizes performance")
    print("✅ Seamless integration with existing Contexa agents")
    print("✅ Robust error handling for distributed scenarios")
    print("✅ Performance optimization techniques for production use")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main()) 