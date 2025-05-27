# MCP Proxy Integration Guide

## Overview

This guide provides comprehensive integration patterns and best practices for using MCP client proxies in different scenarios. Whether you're building a simple single-agent system or a complex distributed architecture, this guide will help you integrate MCP proxies effectively.

## Integration Scenarios

### Scenario 1: Single Agent with Remote Tools

**Use Case:** A single agent that needs to access remote tools hosted on an MCP server.

**Architecture:**
```
[Local Agent] → [MCP Proxy] → [Remote MCP Server] → [Remote Tools]
```

**Implementation:**

```python
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.mcp.client.proxy import MCPProxyConfig
from contexa_sdk.mcp.client.proxy_factory import create_mcp_proxy_factory

async def single_agent_remote_tools():
    """Integrate a single agent with remote tools via MCP proxy."""
    
    # Create local agent
    agent = ContexaAgent(
        name="DataAnalyst",
        description="Agent that analyzes data using remote tools",
        model=ContexaModel(provider="openai", model_id="gpt-4o")
    )
    
    # Configure MCP proxy
    config = MCPProxyConfig(
        server_url="http://analytics-server:8000",
        cache_ttl=300,  # 5-minute cache for analysis results
        enable_caching=True
    )
    
    async with create_mcp_proxy_factory(config) as factory:
        # Create remote tool proxies
        data_loader = await factory.create_tool_proxy("data_loader")
        statistical_analyzer = await factory.create_tool_proxy("statistical_analyzer")
        chart_generator = await factory.create_tool_proxy("chart_generator")
        
        # Agent workflow using remote tools
        async def analyze_dataset(dataset_path: str):
            # Step 1: Load data remotely
            data = await data_loader.execute({"path": dataset_path})
            
            # Step 2: Perform statistical analysis
            stats = await statistical_analyzer.execute({"data": data})
            
            # Step 3: Generate charts
            charts = await chart_generator.execute({
                "data": data,
                "statistics": stats,
                "chart_types": ["histogram", "scatter", "correlation"]
            })
            
            return {
                "data_summary": data,
                "statistics": stats,
                "visualizations": charts
            }
        
        # Execute analysis
        result = await analyze_dataset("/data/sales_2024.csv")
        return result

# Usage
async def main():
    result = await single_agent_remote_tools()
    print(f"Analysis complete: {result}")
```

**Benefits:**
- Offload compute-intensive tasks to specialized servers
- Access to tools without local installation
- Automatic caching for repeated operations
- Transparent error handling and retries

### Scenario 2: Multi-Agent Collaboration with Shared Resources

**Use Case:** Multiple agents collaborating on a task, sharing resources and intermediate results.

**Architecture:**
```
[Agent A] ↘
           [Shared MCP Server] → [Shared Resources]
[Agent B] ↗                   → [Collaboration Tools]
```

**Implementation:**

```python
from contexa_sdk.mcp.client.proxy_factory import MCPProxyFactory
import asyncio

class MultiAgentCollaboration:
    """Coordinate multiple agents using shared MCP resources."""
    
    def __init__(self, mcp_config: MCPProxyConfig):
        self.config = mcp_config
        self.factory = None
        self.shared_workspace = None
    
    async def __aenter__(self):
        self.factory = MCPProxyFactory(self.config)
        self.shared_workspace = await self.factory.create_resource_proxy()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.factory:
            await self.factory.close()
    
    async def create_research_agent(self):
        """Create agent specialized in research tasks."""
        research_tools = [
            await self.factory.create_tool_proxy("web_search"),
            await self.factory.create_tool_proxy("document_analyzer"),
            await self.factory.create_tool_proxy("fact_checker")
        ]
        
        async def research_task(topic: str):
            # Search for information
            search_results = await research_tools[0].execute({"query": topic})
            
            # Analyze documents
            analysis = await research_tools[1].execute({"documents": search_results})
            
            # Fact-check findings
            verified_facts = await research_tools[2].execute({"claims": analysis})
            
            # Store results in shared workspace
            await self.shared_workspace.subscribe_to_resource(f"research/{topic}")
            
            return {
                "topic": topic,
                "findings": verified_facts,
                "sources": search_results
            }
        
        return research_task
    
    async def create_writing_agent(self):
        """Create agent specialized in content creation."""
        writing_tools = [
            await self.factory.create_tool_proxy("content_generator"),
            await self.factory.create_tool_proxy("style_checker"),
            await self.factory.create_tool_proxy("plagiarism_detector")
        ]
        
        async def writing_task(research_data: dict):
            # Generate content based on research
            draft = await writing_tools[0].execute({
                "research": research_data,
                "style": "professional",
                "length": "medium"
            })
            
            # Check style and grammar
            style_feedback = await writing_tools[1].execute({"content": draft})
            
            # Check for plagiarism
            originality_check = await writing_tools[2].execute({"content": draft})
            
            return {
                "content": draft,
                "style_score": style_feedback,
                "originality_score": originality_check
            }
        
        return writing_task
    
    async def collaborative_workflow(self, topic: str):
        """Execute collaborative workflow between agents."""
        
        # Create specialized agents
        researcher = await self.create_research_agent()
        writer = await self.create_writing_agent()
        
        # Phase 1: Research
        print(f"🔍 Starting research on: {topic}")
        research_results = await researcher(topic)
        
        # Phase 2: Content creation
        print(f"✍️ Creating content based on research")
        content_results = await writer(research_results)
        
        # Phase 3: Collaboration and refinement
        print(f"🔄 Refining content through collaboration")
        
        # Use shared resources for feedback loop
        resources = await self.shared_workspace.list_resources()
        collaboration_data = {
            "research": research_results,
            "content": content_results,
            "shared_resources": [r.uri for r in resources]
        }
        
        return collaboration_data

# Usage
async def multi_agent_example():
    config = MCPProxyConfig(
        server_url="http://collaboration-server:8000",
        cache_size=500,  # Large cache for shared resources
        cache_ttl=600    # 10-minute cache for collaboration data
    )
    
    async with MultiAgentCollaboration(config) as collaboration:
        result = await collaboration.collaborative_workflow("Artificial Intelligence in Healthcare")
        return result
```

### Scenario 3: Microservices Architecture with MCP

**Use Case:** Distributed microservices where each service exposes capabilities via MCP.

**Architecture:**
```
[API Gateway] → [Service A (MCP)] → [Database A]
              → [Service B (MCP)] → [ML Models]
              → [Service C (MCP)] → [External APIs]
```

**Implementation:**

```python
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class ServiceConfig:
    name: str
    mcp_url: str
    capabilities: List[str]
    health_check_interval: int = 30

class MicroservicesMCPOrchestrator:
    """Orchestrate multiple microservices via MCP proxies."""
    
    def __init__(self, services: List[ServiceConfig]):
        self.services = services
        self.service_factories = {}
        self.health_status = {}
    
    async def initialize(self):
        """Initialize connections to all microservices."""
        for service in self.services:
            config = MCPProxyConfig(
                server_url=service.mcp_url,
                timeout=20.0,
                max_retries=2,
                headers={"X-Service-Name": service.name}
            )
            
            factory = MCPProxyFactory(config)
            
            # Test connection
            if await factory.validate_connection():
                self.service_factories[service.name] = factory
                self.health_status[service.name] = "healthy"
                print(f"✅ Connected to {service.name}")
            else:
                self.health_status[service.name] = "unhealthy"
                print(f"❌ Failed to connect to {service.name}")
    
    async def get_service_proxy(self, service_name: str, capability: str):
        """Get a proxy for a specific service capability."""
        if service_name not in self.service_factories:
            raise ValueError(f"Service {service_name} not available")
        
        factory = self.service_factories[service_name]
        
        # Create appropriate proxy based on capability type
        if capability.startswith("tool:"):
            tool_name = capability.replace("tool:", "")
            return await factory.create_tool_proxy(tool_name)
        elif capability == "resources":
            return await factory.create_resource_proxy()
        elif capability == "prompts":
            return await factory.create_prompt_proxy()
        else:
            raise ValueError(f"Unknown capability: {capability}")
    
    async def execute_distributed_workflow(self, workflow_definition: Dict):
        """Execute a workflow across multiple microservices."""
        results = {}
        
        for step_name, step_config in workflow_definition["steps"].items():
            service_name = step_config["service"]
            capability = step_config["capability"]
            input_data = step_config.get("input", {})
            
            # Add results from previous steps to input
            if "depends_on" in step_config:
                for dependency in step_config["depends_on"]:
                    if dependency in results:
                        input_data[f"{dependency}_result"] = results[dependency]
            
            try:
                # Get service proxy
                proxy = await self.get_service_proxy(service_name, capability)
                
                # Execute step
                print(f"🔄 Executing {step_name} on {service_name}")
                result = await proxy.execute(input_data)
                results[step_name] = result
                
                print(f"✅ Completed {step_name}")
                
            except Exception as e:
                print(f"❌ Failed {step_name}: {e}")
                results[step_name] = {"error": str(e)}
        
        return results
    
    async def health_check(self):
        """Perform health checks on all services."""
        health_results = {}
        
        for service_name, factory in self.service_factories.items():
            try:
                is_healthy = await factory.validate_connection()
                health_results[service_name] = "healthy" if is_healthy else "unhealthy"
            except Exception as e:
                health_results[service_name] = f"error: {e}"
        
        self.health_status = health_results
        return health_results
    
    async def close(self):
        """Close all service connections."""
        for factory in self.service_factories.values():
            await factory.close()

# Usage example
async def microservices_example():
    # Define microservices
    services = [
        ServiceConfig(
            name="user_service",
            mcp_url="http://user-service:8000",
            capabilities=["tool:get_user", "tool:update_user", "resources"]
        ),
        ServiceConfig(
            name="payment_service", 
            mcp_url="http://payment-service:8000",
            capabilities=["tool:process_payment", "tool:refund", "resources"]
        ),
        ServiceConfig(
            name="notification_service",
            mcp_url="http://notification-service:8000", 
            capabilities=["tool:send_email", "tool:send_sms", "prompts"]
        )
    ]
    
    # Define workflow
    workflow = {
        "name": "user_payment_workflow",
        "steps": {
            "get_user": {
                "service": "user_service",
                "capability": "tool:get_user",
                "input": {"user_id": "12345"}
            },
            "process_payment": {
                "service": "payment_service", 
                "capability": "tool:process_payment",
                "depends_on": ["get_user"],
                "input": {"amount": 99.99, "currency": "USD"}
            },
            "send_confirmation": {
                "service": "notification_service",
                "capability": "tool:send_email", 
                "depends_on": ["get_user", "process_payment"],
                "input": {"template": "payment_confirmation"}
            }
        }
    }
    
    # Execute workflow
    orchestrator = MicroservicesMCPOrchestrator(services)
    await orchestrator.initialize()
    
    try:
        results = await orchestrator.execute_distributed_workflow(workflow)
        print(f"Workflow results: {results}")
        
        # Health check
        health = await orchestrator.health_check()
        print(f"Service health: {health}")
        
    finally:
        await orchestrator.close()
```

### Scenario 4: Edge Computing with MCP Proxies

**Use Case:** Edge devices that need to access cloud-based AI services through MCP.

**Architecture:**
```
[Edge Device] → [Local MCP Proxy] → [Cloud MCP Server] → [AI Services]
              ↓
              [Local Cache] (for offline capability)
```

**Implementation:**

```python
import asyncio
import json
from pathlib import Path

class EdgeMCPProxy:
    """MCP proxy optimized for edge computing scenarios."""
    
    def __init__(self, cloud_config: MCPProxyConfig, local_cache_dir: str):
        self.cloud_config = cloud_config
        self.local_cache_dir = Path(local_cache_dir)
        self.local_cache_dir.mkdir(exist_ok=True)
        self.factory = None
        self.offline_mode = False
    
    async def initialize(self):
        """Initialize connection to cloud services."""
        try:
            self.factory = MCPProxyFactory(self.cloud_config)
            
            # Test cloud connectivity
            if await self.factory.validate_connection():
                print("☁️ Connected to cloud MCP services")
                self.offline_mode = False
            else:
                print("📱 Operating in offline mode")
                self.offline_mode = True
                
        except Exception as e:
            print(f"⚠️ Cloud connection failed, using offline mode: {e}")
            self.offline_mode = True
    
    async def execute_with_fallback(self, tool_name: str, input_data: dict):
        """Execute tool with cloud/local fallback."""
        
        # Generate cache key
        cache_key = f"{tool_name}_{hash(json.dumps(input_data, sort_keys=True))}"
        cache_file = self.local_cache_dir / f"{cache_key}.json"
        
        if not self.offline_mode and self.factory:
            try:
                # Try cloud execution
                tool_proxy = await self.factory.create_tool_proxy(tool_name)
                result = await tool_proxy.execute(input_data)
                
                # Cache result locally
                with open(cache_file, 'w') as f:
                    json.dump({
                        "input": input_data,
                        "result": result,
                        "timestamp": asyncio.get_event_loop().time()
                    }, f)
                
                return result
                
            except Exception as e:
                print(f"☁️ Cloud execution failed: {e}, trying local cache")
        
        # Fallback to local cache
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                print(f"📱 Using cached result for {tool_name}")
                return cached_data["result"]
        
        # No cache available
        raise Exception(f"No cloud connection and no cached result for {tool_name}")
    
    async def sync_cache_when_online(self):
        """Sync local cache with cloud when connection is restored."""
        if self.offline_mode or not self.factory:
            return
        
        print("🔄 Syncing cache with cloud services")
        
        # Process any pending operations
        pending_dir = self.local_cache_dir / "pending"
        if pending_dir.exists():
            for pending_file in pending_dir.glob("*.json"):
                try:
                    with open(pending_file, 'r') as f:
                        pending_op = json.load(f)
                    
                    # Execute pending operation
                    result = await self.execute_with_fallback(
                        pending_op["tool_name"],
                        pending_op["input_data"]
                    )
                    
                    # Remove from pending
                    pending_file.unlink()
                    print(f"✅ Synced pending operation: {pending_file.name}")
                    
                except Exception as e:
                    print(f"❌ Failed to sync {pending_file.name}: {e}")
    
    async def close(self):
        """Close connections."""
        if self.factory:
            await self.factory.close()

# Edge device workflow
async def edge_ai_workflow():
    """Example edge AI workflow with cloud fallback."""
    
    # Configure for edge environment
    cloud_config = MCPProxyConfig(
        server_url="https://ai-cloud.example.com:443",
        timeout=10.0,  # Shorter timeout for edge
        max_retries=1,  # Fewer retries
        cache_size=100,  # Smaller cache
        auth_token="edge_device_token"
    )
    
    edge_proxy = EdgeMCPProxy(cloud_config, "/tmp/edge_cache")
    await edge_proxy.initialize()
    
    try:
        # AI tasks that might need cloud processing
        tasks = [
            ("image_classifier", {"image_path": "/sensors/camera1.jpg"}),
            ("anomaly_detector", {"sensor_data": [1.2, 1.5, 1.1, 2.8, 1.3]}),
            ("predictive_model", {"features": {"temp": 25.5, "humidity": 60.2}})
        ]
        
        results = {}
        for tool_name, input_data in tasks:
            try:
                result = await edge_proxy.execute_with_fallback(tool_name, input_data)
                results[tool_name] = result
                print(f"✅ {tool_name}: {result}")
            except Exception as e:
                print(f"❌ {tool_name} failed: {e}")
                results[tool_name] = {"error": str(e)}
        
        # Sync cache when possible
        await edge_proxy.sync_cache_when_online()
        
        return results
        
    finally:
        await edge_proxy.close()
```

### Scenario 5: Development and Testing Environment

**Use Case:** Setting up MCP proxies for development and testing with mock services.

**Implementation:**

```python
from unittest.mock import AsyncMock
import pytest

class MockMCPServer:
    """Mock MCP server for testing."""
    
    def __init__(self):
        self.tools = {}
        self.resources = {}
        self.prompts = {}
    
    def add_mock_tool(self, name: str, mock_function):
        """Add a mock tool."""
        self.tools[name] = mock_function
    
    def add_mock_resource(self, uri: str, content):
        """Add a mock resource."""
        self.resources[uri] = content
    
    def add_mock_prompt(self, name: str, template):
        """Add a mock prompt template."""
        self.prompts[name] = template

class TestMCPProxyIntegration:
    """Test suite for MCP proxy integration."""
    
    @pytest.fixture
    async def mock_server(self):
        """Create mock MCP server for testing."""
        server = MockMCPServer()
        
        # Add mock tools
        server.add_mock_tool("calculator", lambda x: x["a"] + x["b"])
        server.add_mock_tool("text_analyzer", lambda x: {"word_count": len(x["text"].split())})
        
        # Add mock resources
        server.add_mock_resource("file://test.txt", "Test content")
        server.add_mock_resource("file://data.json", {"test": "data"})
        
        # Add mock prompts
        server.add_mock_prompt("summarize", "Summarize: {text}")
        
        return server
    
    @pytest.mark.asyncio
    async def test_basic_proxy_functionality(self, mock_server):
        """Test basic proxy functionality with mocks."""
        
        # Create test configuration
        config = MCPProxyConfig(
            server_url="http://mock-server:8000",
            enable_caching=True,
            cache_ttl=60
        )
        
        # Mock the actual HTTP calls
        with patch('contexa_sdk.mcp.client.proxy.MCPToolProxy._make_request') as mock_request:
            mock_request.return_value = {"result": 42}
            
            async with create_mcp_proxy_factory(config) as factory:
                # Test tool proxy
                calculator = await factory.create_tool_proxy("calculator")
                result = await calculator.execute({"a": 20, "b": 22})
                
                assert result == 42
                mock_request.assert_called()
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling scenarios."""
        
        config = MCPProxyConfig(
            server_url="http://unreachable-server:8000",
            timeout=1.0,
            max_retries=1
        )
        
        with pytest.raises(Exception):
            async with create_mcp_proxy_factory(config) as factory:
                tool_proxy = await factory.create_tool_proxy("nonexistent_tool")
                await tool_proxy.execute({"test": "data"})
    
    @pytest.mark.asyncio
    async def test_caching_behavior(self):
        """Test caching behavior."""
        
        config = MCPProxyConfig(
            server_url="http://mock-server:8000",
            enable_caching=True,
            cache_ttl=300
        )
        
        call_count = 0
        
        async def mock_execute(data):
            nonlocal call_count
            call_count += 1
            return {"result": f"call_{call_count}"}
        
        with patch('contexa_sdk.mcp.client.proxy.MCPToolProxy._make_request') as mock_request:
            mock_request.side_effect = lambda *args, **kwargs: mock_execute(kwargs.get('data', {}))
            
            async with create_mcp_proxy_factory(config) as factory:
                tool_proxy = await factory.create_tool_proxy("test_tool")
                
                # First call
                result1 = await tool_proxy.execute({"test": "data"})
                
                # Second call with same data (should use cache)
                result2 = await tool_proxy.execute({"test": "data"})
                
                # Verify caching worked
                assert result1 == result2
                assert call_count == 1  # Only one actual call made

# Development utilities
class DevelopmentMCPSetup:
    """Utilities for setting up MCP proxies in development."""
    
    @staticmethod
    def create_dev_config(service_name: str) -> MCPProxyConfig:
        """Create development configuration."""
        return MCPProxyConfig(
            server_url=f"http://localhost:800{hash(service_name) % 10}",
            timeout=5.0,
            enable_caching=True,
            cache_size=50,
            headers={"X-Dev-Mode": "true"}
        )
    
    @staticmethod
    async def setup_development_environment():
        """Set up complete development environment."""
        
        services = ["analytics", "ml_models", "data_processing"]
        factories = {}
        
        for service in services:
            config = DevelopmentMCPSetup.create_dev_config(service)
            factory = MCPProxyFactory(config)
            
            # Test connection (will fail in dev, but that's expected)
            try:
                await factory.validate_connection()
                print(f"✅ {service} service available")
            except:
                print(f"⚠️ {service} service not available (using mocks)")
            
            factories[service] = factory
        
        return factories

# Usage in development
async def development_example():
    """Example of using MCP proxies in development."""
    
    # Set up development environment
    factories = await DevelopmentMCPSetup.setup_development_environment()
    
    try:
        # Use analytics service
        analytics_factory = factories["analytics"]
        
        # Create proxies (will use mocks if service unavailable)
        data_analyzer = await analytics_factory.create_tool_proxy("data_analyzer")
        
        # Test with sample data
        result = await data_analyzer.execute({
            "dataset": "sample_data.csv",
            "analysis_type": "descriptive_statistics"
        })
        
        print(f"Analysis result: {result}")
        
    except Exception as e:
        print(f"Development test failed: {e}")
    
    finally:
        # Cleanup
        for factory in factories.values():
            await factory.close()
```

## Best Practices Summary

### 1. Configuration Management

- **Environment-specific configs**: Use different configurations for dev/staging/prod
- **Connection pooling**: Size pools based on expected concurrency
- **Caching strategy**: Balance cache size, TTL, and memory usage
- **Timeout settings**: Set appropriate timeouts for your network conditions

### 2. Error Handling

- **Graceful degradation**: Implement fallbacks for service unavailability
- **Circuit breakers**: Prevent cascading failures
- **Retry logic**: Use exponential backoff for transient failures
- **Monitoring**: Track error rates and performance metrics

### 3. Performance Optimization

- **Cache warming**: Pre-load frequently used data
- **Batch operations**: Group related operations for efficiency
- **Connection reuse**: Leverage connection pooling
- **Load balancing**: Distribute load across multiple servers

### 4. Security Considerations

- **Authentication**: Use proper authentication tokens
- **Encryption**: Ensure TLS/SSL for production
- **Access control**: Implement proper authorization
- **Audit logging**: Track all proxy operations

### 5. Testing Strategy

- **Unit tests**: Test individual proxy components
- **Integration tests**: Test end-to-end workflows
- **Mock services**: Use mocks for development and testing
- **Performance tests**: Validate performance under load

## Conclusion

MCP proxies provide a powerful foundation for building distributed agent architectures. By following the integration patterns and best practices outlined in this guide, you can build robust, scalable, and maintainable systems that leverage remote capabilities transparently.

Choose the integration pattern that best fits your use case:
- **Single Agent**: Simple remote tool access
- **Multi-Agent**: Collaborative workflows with shared resources
- **Microservices**: Distributed service architecture
- **Edge Computing**: Cloud/local hybrid deployments
- **Development**: Testing and development environments

For additional guidance or specific integration questions, refer to the Contexa SDK documentation or reach out to the development team. 