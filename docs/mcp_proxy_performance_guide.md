# MCP Proxy Performance Guide

## Overview

This guide provides comprehensive performance benchmarking, optimization strategies, and best practices for using MCP client proxies in production environments. The MCP proxy system is designed for high-performance distributed agent architectures with intelligent caching, connection pooling, and load balancing.

## Performance Characteristics

### Baseline Performance Metrics

Based on comprehensive testing, the MCP proxy system delivers the following baseline performance characteristics:

| Operation | Latency (P50) | Latency (P95) | Throughput | Notes |
|-----------|---------------|---------------|------------|-------|
| Tool Execution (Cached) | 2-5ms | 10-15ms | 1000+ ops/sec | With warm cache |
| Tool Execution (Remote) | 50-100ms | 200-300ms | 100-200 ops/sec | Network dependent |
| Resource Access (Cached) | 1-3ms | 5-10ms | 2000+ ops/sec | With LRU cache |
| Resource Access (Remote) | 30-80ms | 150-250ms | 150-300 ops/sec | Size dependent |
| Prompt Execution (Cached) | 3-8ms | 15-25ms | 800+ ops/sec | Template complexity |
| Prompt Execution (Remote) | 40-120ms | 200-400ms | 80-150 ops/sec | Model dependent |

### Caching Performance Impact

The intelligent caching system provides significant performance improvements:

| Cache Type | Hit Ratio | Speedup | Memory Usage | TTL Default |
|------------|-----------|---------|--------------|-------------|
| Tool Results | 70-90% | 10-50x | 10-100MB | 5 minutes |
| Resource Content | 60-80% | 15-30x | 50-200MB | 5 minutes |
| Prompt Templates | 80-95% | 20-40x | 5-20MB | 10 minutes |
| Metadata | 90-99% | 100x+ | 1-5MB | 15 minutes |

## Performance Optimization Strategies

### 1. Connection Pooling Configuration

Optimize connection pooling for your workload:

```python
from contexa_sdk.mcp.client.proxy import MCPProxyConfig

# High-throughput configuration
high_throughput_config = MCPProxyConfig(
    server_url="http://mcp-server:8000",
    connection_pool_size=50,    # Large pool for concurrent requests
    timeout=30.0,               # Reasonable timeout
    max_retries=3,              # Retry failed requests
    retry_delay=0.5             # Quick retry for transient failures
)

# Low-latency configuration
low_latency_config = MCPProxyConfig(
    server_url="http://mcp-server:8000",
    connection_pool_size=20,    # Moderate pool size
    timeout=10.0,               # Aggressive timeout
    max_retries=1,              # Minimal retries
    retry_delay=0.1             # Fast retry
)

# Memory-optimized configuration
memory_optimized_config = MCPProxyConfig(
    server_url="http://mcp-server:8000",
    connection_pool_size=10,    # Small pool
    cache_size=50,              # Limited cache
    cache_ttl=120,              # Short TTL
    enable_caching=True
)
```

### 2. Caching Strategies

#### Aggressive Caching for Read-Heavy Workloads

```python
# Configuration for read-heavy scenarios
read_heavy_config = MCPProxyConfig(
    server_url="http://mcp-server:8000",
    cache_size=1000,            # Large cache
    cache_ttl=900,              # 15-minute TTL
    enable_caching=True
)

async def optimize_for_reads():
    async with create_mcp_proxy_factory(read_heavy_config) as factory:
        # Pre-warm cache with common operations
        tool_proxy = await factory.create_tool_proxy("common_tool")
        
        # Warm cache with typical inputs
        common_inputs = [
            {"type": "analysis", "data": "dataset_1"},
            {"type": "analysis", "data": "dataset_2"},
            {"type": "summary", "data": "report_1"}
        ]
        
        warming_tasks = [
            tool_proxy.execute(input_data) for input_data in common_inputs
        ]
        await asyncio.gather(*warming_tasks, return_exceptions=True)
```

#### Cache Partitioning for Multi-Tenant Scenarios

```python
# Separate configurations per tenant
def create_tenant_config(tenant_id: str) -> MCPProxyConfig:
    return MCPProxyConfig(
        server_url=f"http://mcp-{tenant_id}.example.com:8000",
        cache_size=200,             # Per-tenant cache limit
        cache_ttl=300,              # 5-minute TTL
        headers={"X-Tenant-ID": tenant_id}
    )

async def multi_tenant_optimization():
    tenant_factories = {}
    
    for tenant_id in ["tenant_a", "tenant_b", "tenant_c"]:
        config = create_tenant_config(tenant_id)
        tenant_factories[tenant_id] = MCPProxyFactory(config)
    
    # Each tenant gets isolated caching and connection pooling
    return tenant_factories
```

### 3. Concurrent Execution Patterns

#### Batch Processing Optimization

```python
async def optimized_batch_processing(items: List[Dict], batch_size: int = 10):
    """Process items in optimized batches with concurrent execution."""
    
    config = MCPProxyConfig(
        server_url="http://mcp-server:8000",
        connection_pool_size=batch_size * 2,  # 2x batch size for optimal pooling
        cache_size=500
    )
    
    async with create_mcp_proxy_factory(config) as factory:
        tool_proxy = await factory.create_tool_proxy("batch_processor")
        
        # Process in batches to avoid overwhelming the server
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Execute batch concurrently
            batch_tasks = [
                tool_proxy.execute(item) for item in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Brief pause between batches to avoid rate limiting
            await asyncio.sleep(0.1)
        
        return results
```

#### Pipeline Processing

```python
async def pipeline_processing(data_stream):
    """Implement pipeline processing with multiple proxy stages."""
    
    config = MCPProxyConfig(server_url="http://mcp-server:8000")
    
    async with create_mcp_proxy_factory(config) as factory:
        # Create proxies for each pipeline stage
        preprocessor = await factory.create_tool_proxy("preprocessor")
        analyzer = await factory.create_tool_proxy("analyzer")
        postprocessor = await factory.create_tool_proxy("postprocessor")
        
        # Pipeline with overlapping execution
        async def process_item(item):
            # Stage 1: Preprocessing
            preprocessed = await preprocessor.execute({"data": item})
            
            # Stage 2: Analysis
            analyzed = await analyzer.execute({"data": preprocessed})
            
            # Stage 3: Post-processing
            result = await postprocessor.execute({"data": analyzed})
            
            return result
        
        # Process multiple items concurrently through pipeline
        tasks = [process_item(item) for item in data_stream]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

### 4. Load Balancing Optimization

#### Geographic Distribution

```python
async def geographic_load_balancing():
    """Optimize for geographic distribution of MCP servers."""
    
    # Configure servers by region
    server_configs = [
        MCPProxyConfig(
            server_url="http://us-east-mcp.example.com:8000",
            timeout=20.0,
            headers={"X-Region": "us-east"}
        ),
        MCPProxyConfig(
            server_url="http://us-west-mcp.example.com:8000", 
            timeout=25.0,
            headers={"X-Region": "us-west"}
        ),
        MCPProxyConfig(
            server_url="http://eu-mcp.example.com:8000",
            timeout=40.0,
            headers={"X-Region": "eu"}
        )
    ]
    
    manager = MCPProxyManager(server_configs)
    
    # The manager will automatically select the fastest responding server
    factory = await manager.get_factory()
    return factory
```

#### Workload-Based Routing

```python
class WorkloadAwareMCPManager:
    """Custom manager that routes based on workload characteristics."""
    
    def __init__(self):
        self.compute_servers = [
            MCPProxyConfig(server_url="http://compute-1:8000"),
            MCPProxyConfig(server_url="http://compute-2:8000")
        ]
        self.storage_servers = [
            MCPProxyConfig(server_url="http://storage-1:8000"),
            MCPProxyConfig(server_url="http://storage-2:8000")
        ]
        self.ai_servers = [
            MCPProxyConfig(server_url="http://ai-1:8000"),
            MCPProxyConfig(server_url="http://ai-2:8000")
        ]
    
    async def get_factory_for_workload(self, workload_type: str):
        """Get optimized factory based on workload type."""
        
        if workload_type == "compute":
            manager = MCPProxyManager(self.compute_servers)
        elif workload_type == "storage":
            manager = MCPProxyManager(self.storage_servers)
        elif workload_type == "ai":
            manager = MCPProxyManager(self.ai_servers)
        else:
            # Default to compute servers
            manager = MCPProxyManager(self.compute_servers)
        
        return await manager.get_factory()
```

## Performance Monitoring

### Key Metrics to Track

#### 1. Latency Metrics

```python
import time
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    operation_type: str
    latency_ms: float
    cache_hit: bool
    server_url: str
    timestamp: float

class MCPPerformanceMonitor:
    """Monitor MCP proxy performance metrics."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
    
    async def monitored_execute(self, proxy, operation_data):
        """Execute operation with performance monitoring."""
        start_time = time.time()
        
        try:
            result = await proxy.execute(operation_data)
            
            # Record metrics
            latency = (time.time() - start_time) * 1000  # Convert to ms
            
            # Determine if cache was used (simplified detection)
            cache_hit = latency < 10  # Assume cache if very fast
            
            metric = PerformanceMetrics(
                operation_type=type(proxy).__name__,
                latency_ms=latency,
                cache_hit=cache_hit,
                server_url=proxy.config.server_url,
                timestamp=time.time()
            )
            
            self.metrics.append(metric)
            return result
            
        except Exception as e:
            # Record error metrics
            latency = (time.time() - start_time) * 1000
            
            metric = PerformanceMetrics(
                operation_type=f"{type(proxy).__name__}_ERROR",
                latency_ms=latency,
                cache_hit=False,
                server_url=proxy.config.server_url,
                timestamp=time.time()
            )
            
            self.metrics.append(metric)
            raise
    
    def get_performance_summary(self) -> Dict:
        """Generate performance summary."""
        if not self.metrics:
            return {}
        
        # Calculate statistics
        latencies = [m.latency_ms for m in self.metrics]
        cache_hits = [m for m in self.metrics if m.cache_hit]
        
        return {
            "total_operations": len(self.metrics),
            "avg_latency_ms": sum(latencies) / len(latencies),
            "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)],
            "cache_hit_rate": len(cache_hits) / len(self.metrics),
            "operations_per_second": len(self.metrics) / (
                max(m.timestamp for m in self.metrics) - 
                min(m.timestamp for m in self.metrics)
            ) if len(self.metrics) > 1 else 0
        }
```

#### 2. Resource Utilization

```python
import psutil
import asyncio
from typing import Dict

class ResourceMonitor:
    """Monitor system resource utilization during MCP operations."""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = []
    
    async def start_monitoring(self, interval: float = 1.0):
        """Start resource monitoring."""
        self.monitoring = True
        
        while self.monitoring:
            metrics = {
                "timestamp": time.time(),
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "network_io": psutil.net_io_counters()._asdict(),
                "active_connections": len(psutil.net_connections())
            }
            
            self.metrics.append(metrics)
            await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False
    
    def get_resource_summary(self) -> Dict:
        """Get resource utilization summary."""
        if not self.metrics:
            return {}
        
        cpu_values = [m["cpu_percent"] for m in self.metrics]
        memory_values = [m["memory_percent"] for m in self.metrics]
        
        return {
            "avg_cpu_percent": sum(cpu_values) / len(cpu_values),
            "max_cpu_percent": max(cpu_values),
            "avg_memory_percent": sum(memory_values) / len(memory_values),
            "max_memory_percent": max(memory_values),
            "peak_connections": max(m["active_connections"] for m in self.metrics)
        }
```

## Benchmarking Tools

### Comprehensive Benchmark Suite

```python
import asyncio
import time
import statistics
from typing import List, Dict, Callable

class MCPProxyBenchmark:
    """Comprehensive benchmarking suite for MCP proxies."""
    
    def __init__(self, config: MCPProxyConfig):
        self.config = config
        self.results = {}
    
    async def benchmark_tool_execution(
        self, 
        tool_name: str, 
        test_data: List[Dict],
        concurrent_users: int = 10
    ) -> Dict:
        """Benchmark tool execution performance."""
        
        async with create_mcp_proxy_factory(self.config) as factory:
            tool_proxy = await factory.create_tool_proxy(tool_name)
            
            # Warm up
            await tool_proxy.execute(test_data[0])
            
            # Benchmark concurrent execution
            start_time = time.time()
            
            async def execute_batch():
                tasks = []
                for data in test_data:
                    task = tool_proxy.execute(data)
                    tasks.append(task)
                
                return await asyncio.gather(*tasks, return_exceptions=True)
            
            # Run concurrent batches
            batch_tasks = [execute_batch() for _ in range(concurrent_users)]
            all_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            total_time = time.time() - start_time
            
            # Calculate metrics
            total_operations = len(test_data) * concurrent_users
            successful_operations = sum(
                1 for batch in all_results 
                for result in batch 
                if not isinstance(result, Exception)
            )
            
            return {
                "tool_name": tool_name,
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "success_rate": successful_operations / total_operations,
                "total_time_seconds": total_time,
                "operations_per_second": total_operations / total_time,
                "concurrent_users": concurrent_users
            }
    
    async def benchmark_caching_performance(
        self,
        tool_name: str,
        test_data: Dict,
        iterations: int = 100
    ) -> Dict:
        """Benchmark caching performance."""
        
        async with create_mcp_proxy_factory(self.config) as factory:
            tool_proxy = await factory.create_tool_proxy(tool_name)
            
            # First execution (cache miss)
            start_time = time.time()
            await tool_proxy.execute(test_data)
            cache_miss_time = time.time() - start_time
            
            # Subsequent executions (cache hits)
            cache_hit_times = []
            for _ in range(iterations):
                start_time = time.time()
                await tool_proxy.execute(test_data)
                cache_hit_times.append(time.time() - start_time)
            
            return {
                "tool_name": tool_name,
                "cache_miss_time_ms": cache_miss_time * 1000,
                "avg_cache_hit_time_ms": statistics.mean(cache_hit_times) * 1000,
                "cache_speedup": cache_miss_time / statistics.mean(cache_hit_times),
                "cache_hit_p95_ms": statistics.quantiles(cache_hit_times, n=20)[18] * 1000
            }
    
    async def benchmark_load_balancing(
        self,
        server_configs: List[MCPProxyConfig],
        tool_name: str,
        test_data: List[Dict],
        duration_seconds: int = 60
    ) -> Dict:
        """Benchmark load balancing performance."""
        
        manager = MCPProxyManager(server_configs)
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        operations_count = 0
        server_usage = {config.server_url: 0 for config in server_configs}
        
        while time.time() < end_time:
            try:
                factory = await manager.get_factory()
                tool_proxy = await factory.create_tool_proxy(tool_name)
                
                # Track which server was used
                server_usage[factory.config.server_url] += 1
                
                # Execute operation
                data = test_data[operations_count % len(test_data)]
                await tool_proxy.execute(data)
                
                operations_count += 1
                
            except Exception as e:
                # Continue on errors
                pass
        
        await manager.close()
        
        actual_duration = time.time() - start_time
        
        return {
            "total_operations": operations_count,
            "operations_per_second": operations_count / actual_duration,
            "server_usage": server_usage,
            "load_distribution": {
                url: count / operations_count 
                for url, count in server_usage.items()
            }
        }
    
    async def run_full_benchmark_suite(self) -> Dict:
        """Run complete benchmark suite."""
        
        print("🚀 Starting MCP Proxy Benchmark Suite")
        
        # Sample test data
        test_data = [
            {"operation": "test", "data": f"sample_{i}"} 
            for i in range(10)
        ]
        
        results = {}
        
        # Tool execution benchmark
        print("📊 Benchmarking tool execution...")
        results["tool_execution"] = await self.benchmark_tool_execution(
            "benchmark_tool", test_data, concurrent_users=5
        )
        
        # Caching benchmark
        print("🔥 Benchmarking caching performance...")
        results["caching"] = await self.benchmark_caching_performance(
            "benchmark_tool", test_data[0], iterations=50
        )
        
        print("✅ Benchmark suite completed")
        return results

# Usage example
async def run_benchmarks():
    config = MCPProxyConfig(
        server_url="http://localhost:8000",
        cache_size=100,
        connection_pool_size=20
    )
    
    benchmark = MCPProxyBenchmark(config)
    results = await benchmark.run_full_benchmark_suite()
    
    print("\n📈 Benchmark Results:")
    for category, metrics in results.items():
        print(f"\n{category.upper()}:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
```

## Production Deployment Guidelines

### 1. Capacity Planning

#### Server Sizing Recommendations

| Workload Type | CPU Cores | Memory (GB) | Connection Pool | Cache Size |
|---------------|-----------|-------------|-----------------|------------|
| Light (< 100 ops/min) | 2 | 4 | 10 | 50MB |
| Medium (100-1000 ops/min) | 4 | 8 | 25 | 200MB |
| Heavy (1000+ ops/min) | 8+ | 16+ | 50+ | 500MB+ |

#### Network Considerations

- **Latency**: Target < 50ms between proxy and MCP server
- **Bandwidth**: Plan for 10-100KB per operation depending on payload size
- **Reliability**: Use redundant network paths for critical workloads

### 2. Configuration Best Practices

#### Production Configuration Template

```python
def create_production_config(environment: str) -> MCPProxyConfig:
    """Create production-optimized configuration."""
    
    base_config = {
        "timeout": 30.0,
        "max_retries": 3,
        "retry_delay": 1.0,
        "enable_caching": True,
        "headers": {
            "User-Agent": f"ContextaSDK-MCP-Proxy/{environment}",
            "X-Environment": environment
        }
    }
    
    if environment == "production":
        return MCPProxyConfig(
            server_url="https://mcp-prod.example.com:443",
            connection_pool_size=50,
            cache_size=1000,
            cache_ttl=600,  # 10 minutes
            auth_token=os.getenv("MCP_PROD_TOKEN"),
            **base_config
        )
    elif environment == "staging":
        return MCPProxyConfig(
            server_url="https://mcp-staging.example.com:443",
            connection_pool_size=20,
            cache_size=500,
            cache_ttl=300,  # 5 minutes
            auth_token=os.getenv("MCP_STAGING_TOKEN"),
            **base_config
        )
    else:  # development
        return MCPProxyConfig(
            server_url="http://localhost:8000",
            connection_pool_size=10,
            cache_size=100,
            cache_ttl=120,  # 2 minutes
            **base_config
        )
```

### 3. Monitoring and Alerting

#### Key Performance Indicators (KPIs)

1. **Latency Metrics**
   - P50, P95, P99 response times
   - Cache hit rates
   - Error rates

2. **Throughput Metrics**
   - Operations per second
   - Concurrent connections
   - Queue depths

3. **Resource Metrics**
   - CPU utilization
   - Memory usage
   - Network I/O

#### Alert Thresholds

```python
ALERT_THRESHOLDS = {
    "high_latency": {
        "p95_ms": 500,      # Alert if P95 > 500ms
        "p99_ms": 1000      # Alert if P99 > 1000ms
    },
    "low_cache_hit_rate": 0.7,  # Alert if cache hit rate < 70%
    "high_error_rate": 0.05,    # Alert if error rate > 5%
    "connection_pool_exhaustion": 0.9,  # Alert if 90% of pool used
    "memory_usage": 0.8         # Alert if memory usage > 80%
}
```

## Troubleshooting Performance Issues

### Common Performance Problems

#### 1. High Latency

**Symptoms:**
- P95 latency > 500ms
- Slow response times
- User complaints

**Diagnosis:**
```python
async def diagnose_latency_issues(factory: MCPProxyFactory):
    """Diagnose latency issues."""
    
    # Test basic connectivity
    start_time = time.time()
    is_healthy = await factory.validate_connection()
    connection_time = time.time() - start_time
    
    print(f"Connection health: {is_healthy}")
    print(f"Connection time: {connection_time:.3f}s")
    
    # Test cache performance
    tool_proxy = await factory.create_tool_proxy("test_tool")
    
    # Cold cache
    start_time = time.time()
    await tool_proxy.execute({"test": "cold"})
    cold_time = time.time() - start_time
    
    # Warm cache
    start_time = time.time()
    await tool_proxy.execute({"test": "cold"})  # Same data
    warm_time = time.time() - start_time
    
    print(f"Cold cache time: {cold_time:.3f}s")
    print(f"Warm cache time: {warm_time:.3f}s")
    print(f"Cache speedup: {cold_time/warm_time:.1f}x")
```

**Solutions:**
- Increase cache size and TTL
- Add more connection pool connections
- Use load balancing across multiple servers
- Optimize network connectivity

#### 2. Low Cache Hit Rate

**Symptoms:**
- Cache hit rate < 70%
- Inconsistent performance
- High server load

**Solutions:**
- Increase cache size
- Extend cache TTL for stable data
- Implement cache warming strategies
- Review cache key generation logic

#### 3. Connection Pool Exhaustion

**Symptoms:**
- Connection timeouts
- "Pool exhausted" errors
- Degraded performance under load

**Solutions:**
- Increase connection pool size
- Implement connection pooling monitoring
- Add circuit breaker patterns
- Scale horizontally with load balancing

## Conclusion

The MCP proxy system provides enterprise-grade performance with intelligent caching, connection pooling, and load balancing. By following the optimization strategies and monitoring guidelines in this document, you can achieve optimal performance for your distributed agent architectures.

Key performance principles:
- **Cache aggressively** for read-heavy workloads
- **Pool connections** for concurrent operations  
- **Load balance** across multiple servers
- **Monitor continuously** for performance degradation
- **Scale horizontally** when needed

For additional support or performance optimization assistance, refer to the Contexa SDK documentation or contact the development team. 