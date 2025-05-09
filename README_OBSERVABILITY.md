# Observability in Contexa SDK

The Contexa SDK provides comprehensive observability features to monitor and debug your agents. These features give you detailed insights into agent executions, tool calls, model responses, and more.

## Overview

The observability module includes three main components:

1. **Logging** - Structured logs with context information
2. **Tracing** - Distributed tracing for detailed execution paths
3. **Metrics** - Performance and operational metrics

## Logging

The logging system provides structured logs with rich context information. This makes it easier to understand what's happening with your agents and helps with debugging.

### Basic Usage

```python
from contexa_sdk.observability import get_logger

# Create a logger for your module
logger = get_logger(__name__)

# Log various levels with context
logger.info("Agent starting", extra={"agent_id": agent_id})
logger.error("Connection failed", extra={"endpoint": url, "status_code": 500})

# Log with structured context
logger.info_with_context("Operation completed", {
    "operation_id": "123",
    "duration_ms": 456,
    "user_id": "user-789"
})
```

### Configuration

Control logging behavior with environment variables:

- `CONTEXA_LOG_LEVEL` - Sets the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `CONTEXA_LOG_FORMAT` - Sets the log format (default: text, JSON for structured output)

```bash
export CONTEXA_LOG_LEVEL=DEBUG
export CONTEXA_LOG_FORMAT=JSON
```

## Tracing

Tracing provides detailed information about the execution path of your agents, including timing, relationships between operations, and more.

### Basic Usage

```python
from contexa_sdk.observability import trace, Span, SpanKind

# Decorate functions to automatically trace them
@trace(kind=SpanKind.AGENT)
async def my_agent_function(query):
    # Will be automatically traced
    return result

# Use spans manually for more control
with Span(name="my_operation", kind=SpanKind.TOOL) as span:
    # Set attributes to add context
    span.set_attribute("operation.type", "database_query")
    span.set_attribute("query.parameters", json.dumps(params))
    
    # Perform the operation
    result = await perform_operation()
    
    # Record the result
    span.set_attribute("operation.result", "success" if result else "failure")
```

### Span Types

The SDK defines several span kinds for different operations:

- `SpanKind.AGENT` - Agent operations
- `SpanKind.TOOL` - Tool calls
- `SpanKind.MODEL` - Model API calls
- `SpanKind.HANDOFF` - Agent handoffs
- `SpanKind.INTERNAL` - General internal operations
- `SpanKind.CLIENT` - Client requests
- `SpanKind.SERVER` - Server responses

### Configuration

Control tracing behavior with environment variables:

- `CONTEXA_TRACE_EXPORTER` - Sets the trace exporter (console, file, otlp)
- `CONTEXA_TRACE_DIR` - Directory to store trace files (when using file exporter)

```bash
export CONTEXA_TRACE_EXPORTER=file
export CONTEXA_TRACE_DIR=./.ctx/traces
```

## Metrics

Metrics provide aggregated data about your agent operations, including latency, token usage, and more.

### Built-in Metrics

The SDK includes several built-in metrics:

- `agent_requests_total` - Total number of agent requests
- `agent_latency_seconds` - Latency of agent requests
- `model_tokens_total` - Total tokens used by models
- `tool_calls_total` - Total number of tool calls
- `tool_latency_seconds` - Latency of tool calls
- `handoffs_total` - Total number of agent handoffs
- `active_agents` - Number of currently active agents

### Recording Custom Metrics

```python
from contexa_sdk.observability import record_metric, Timer
from contexa_sdk.observability.metrics import counter, gauge, histogram

# Simple metric recording
record_metric("counter", "my_counter", 1, "My custom counter", {"label1": "value1"})

# Use specific metric types
my_counter = counter("operations_total", "Total operations performed", ["operation_type"])
my_counter.inc(1, operation_type="query")

my_gauge = gauge("queue_size", "Number of items in queue")
my_gauge.set(10)

my_histogram = histogram("response_size_bytes", "Size of responses in bytes")
my_histogram.observe(1024)

# Timing operations
with Timer(my_histogram, operation_type="query") as timer:
    # Perform operation
    result = perform_operation()
```

### Configuration

Control metrics behavior with environment variables:

- `CONTEXA_METRICS_EXPORTER` - Sets the metrics exporter (console, file, prometheus)
- `CONTEXA_METRICS_DIR` - Directory to store metrics files (when using file exporter)
- `CONTEXA_METRICS_FLUSH_INTERVAL` - Interval in seconds to flush metrics (default: 60)
- `CONTEXA_METRICS_AUTO_START` - Whether to auto-start metrics collection (default: true)

```bash
export CONTEXA_METRICS_EXPORTER=file
export CONTEXA_METRICS_DIR=./.ctx/metrics
export CONTEXA_METRICS_FLUSH_INTERVAL=30
```

## Integration with External Systems

The Contexa SDK's observability features are designed to work with popular external systems:

### OpenTelemetry Integration

The tracing system is compatible with OpenTelemetry, allowing you to export traces to systems like Jaeger, Zipkin, or any other OpenTelemetry-compatible system.

```python
# Future feature - setting up OpenTelemetry export
```

### Prometheus Integration

Metrics can be exported to Prometheus for monitoring and alerting.

```python
# Future feature - setting up Prometheus export
```

## Visualizing Tracing Data

You can visualize your traces using any OpenTelemetry-compatible visualization tool. For a quick local view, the file-based traces can be converted to a browser-viewable format:

```python
from contexa_sdk.observability.viewers import create_trace_visualization

# Generate an HTML file to view traces
create_trace_visualization(
    trace_dir="./.ctx/traces",
    output_file="./traces.html"
)
```

## Best Practices

1. **Use standard span kinds** - Use the provided SpanKind values for consistency
2. **Add context to logs** - Include relevant context in log messages
3. **Label metrics appropriately** - Add meaningful labels to metrics
4. **Use tracing for complex workflows** - Trace complex operations to understand bottlenecks
5. **Monitor token usage** - Keep an eye on token usage metrics to control costs 