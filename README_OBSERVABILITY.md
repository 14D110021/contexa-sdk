# Observability

The Contexa SDK provides comprehensive observability capabilities for monitoring, debugging, and analyzing agent behavior. These features help developers understand what's happening inside their agents, identify issues, and optimize performance.

## Key Observability Features

- **Structured Logging**: Track agent operations with detailed, structured logs
- **Metrics Collection**: Monitor performance and usage metrics
- **Tracing**: Follow request flows through multiple agents and tools
- **OpenTelemetry Compatible**: Integrate with existing observability stacks

## Logging

### Basic Logging Setup

```python
from contexa_sdk.observability.logging import configure_logging

# Configure basic logging
configure_logging(
    level="INFO",  # Log level: DEBUG, INFO, WARNING, ERROR
    output_format="json",  # Output format: json or text
    log_file="agent.log"  # Optional file to write logs
)

# Create an agent with logging
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel

agent = ContexaAgent(
    name="My Assistant",
    description="A helpful assistant",
    model=ContexaModel(provider="openai", model_id="gpt-4o"),
    tools=[],
    enable_logging=True  # Enable detailed logging
)
```

### Structured Log Events

The SDK generates structured logs for key events:

```json
{
  "timestamp": "2023-05-15T14:32:17Z",
  "level": "INFO",
  "event": "agent.run.start",
  "agent_id": "agent-1234",
  "agent_name": "My Assistant",
  "input": "What's the weather today?",
  "trace_id": "trace-5678"
}
```

### Custom Log Events

Add custom log events for your specific needs:

```python
from contexa_sdk.observability.logging import log_event

# Log a custom event
log_event(
    event="custom.processing",
    level="INFO",
    data={
        "step": "data_extraction",
        "status": "success",
        "extracted_entities": ["New York", "weather"]
    }
)
```

## Metrics

### Collecting Metrics

```python
from contexa_sdk.observability.metrics import MetricsCollector

# Create a metrics collector
metrics = MetricsCollector()

# Record metrics
metrics.record_counter("agent.runs.total", 1, tags={"agent_id": "agent-1234"})
metrics.record_gauge("agent.memory.usage_mb", 250, tags={"agent_id": "agent-1234"})
metrics.record_histogram("agent.response_time_ms", 320, tags={"agent_id": "agent-1234"})

# Record latency using context manager
with metrics.measure_latency("tool.execution_time_ms", tags={"tool_id": "web_search"}):
    # Code to measure
    result = await web_search(query="example query")
```

### Available Metrics

The SDK automatically collects key metrics:

| Metric Name | Type | Description |
|-------------|------|-------------|
| `agent.runs.total` | Counter | Total number of agent runs |
| `agent.runs.success` | Counter | Successful agent runs |
| `agent.runs.error` | Counter | Failed agent runs |
| `agent.response_time_ms` | Histogram | Agent response time in milliseconds |
| `tool.calls.total` | Counter | Total number of tool calls |
| `tool.calls.success` | Counter | Successful tool calls |
| `tool.calls.error` | Counter | Failed tool calls |
| `tool.execution_time_ms` | Histogram | Tool execution time in milliseconds |
| `model.tokens.input` | Counter | Number of input tokens sent to the model |
| `model.tokens.output` | Counter | Number of output tokens received from the model |
| `model.calls.total` | Counter | Total number of model API calls |
| `model.latency_ms` | Histogram | Model API latency in milliseconds |

### Exporting Metrics

Export metrics to various backends:

```python
# Export to Prometheus
from contexa_sdk.observability.exporters import PrometheusExporter

prometheus = PrometheusExporter(port=9090)
metrics.add_exporter(prometheus)

# Export to OpenTelemetry
from contexa_sdk.observability.exporters import OTelMetricsExporter

otel = OTelMetricsExporter(
    endpoint="https://otel-collector.example.com:4317"
)
metrics.add_exporter(otel)
```

## Tracing

### Trace Context

Track requests across components with trace context:

```python
from contexa_sdk.observability.tracing import Tracer, TraceContext

# Create a tracer
tracer = Tracer()

# Start a new trace
with tracer.start_span("agent.run") as span:
    # Add attributes to the span
    span.set_attribute("agent_id", "agent-1234")
    span.set_attribute("input", "What's the weather today?")
    
    # Create a nested span for a tool call
    with tracer.start_span("tool.execute", parent=span) as tool_span:
        tool_span.set_attribute("tool_id", "web_search")
        tool_span.set_attribute("tool_name", "Web Search")
        
        # Execute the tool
        result = await web_search(query="weather today")
        
        tool_span.set_attribute("status", "success")
```

### Automatic Tracing

The SDK can automatically trace agent and tool operations:

```python
from contexa_sdk.observability.tracing import configure_tracing

# Enable automatic tracing
configure_tracing(
    service_name="my-agent-service",
    enable_auto_instrumentation=True
)

# Create an agent with auto-tracing
agent = ContexaAgent(
    name="My Assistant",
    description="A helpful assistant",
    model=ContexaModel(provider="openai", model_id="gpt-4o"),
    tools=[web_search],
    enable_tracing=True  # Enable automatic tracing
)
```

### Trace Exporters

Export traces to various backends:

```python
from contexa_sdk.observability.exporters import JaegerExporter

# Export traces to Jaeger
jaeger = JaegerExporter(
    endpoint="http://jaeger-collector:14268/api/traces"
)
tracer.add_exporter(jaeger)

# Export traces to OpenTelemetry
from contexa_sdk.observability.exporters import OTelTracesExporter

otel = OTelTracesExporter(
    endpoint="https://otel-collector.example.com:4317"
)
tracer.add_exporter(otel)
```

## OpenTelemetry Integration

Integrate with the OpenTelemetry ecosystem:

```python
from contexa_sdk.observability import configure_opentelemetry

# Configure OpenTelemetry integration
configure_opentelemetry(
    service_name="contexa-agent-service",
    exporter="otlp",  # Options: otlp, jaeger, zipkin
    endpoint="https://otel-collector.example.com:4317",
    enable_metrics=True,
    enable_traces=True,
    enable_logs=True
)
```

## Dashboard & Visualization

The SDK includes pre-built dashboards for popular monitoring systems:

- **Grafana**: Import dashboards from `contexa_sdk/observability/dashboards/grafana`
- **Datadog**: Use templates from `contexa_sdk/observability/dashboards/datadog`
- **Elasticsearch/Kibana**: Import from `contexa_sdk/observability/dashboards/kibana`

## Agent Visualization

Contexa SDK provides powerful visualization tools to help understand your agent architecture, tools, and communication patterns:

```python
from contexa_sdk.observability import draw_graph, get_agent_team_graph, export_graph_to_json

# Visualize an agent's structure (with its tools and handoffs)
draw_graph(
    agent,
    filename="agent_graph",  # Optional: save to a file
    format="png",            # Output format: png, svg, pdf, etc.
    theme="light",           # Theme: light or dark
    show_labels=True,        # Show labels on edges
    include_tools=True,      # Include tool nodes
    include_handoffs=True    # Include handoff relationships
)

# Visualize a team of agents
get_agent_team_graph(
    [agent1, agent2, agent3],
    team_name="Analytics Team",
    filename="team_graph"
)

# Export to JSON for web visualization
graph_data = export_graph_to_json(
    agent,
    filename="agent_graph.json"
)
```

### Installation

The visualization features require additional dependencies:

```bash
pip install contexa-sdk[viz]
```

### Customization

You can customize the visualization appearance:

- **Themes**: Choose between light and dark themes
- **Formats**: Generate PNG, SVG, PDF, or other formats
- **Layout**: Control node shapes, colors, and edge styles
- **Export**: Export to JSON for custom web visualizations using D3.js, Cytoscape, etc.

### Runtime Handoffs

The visualization can capture runtime handoffs between agents, showing the actual communication flow during execution:

```python
# Run agents with handoffs
await orchestrator.handoff(target_agent=researcher, query="Research climate change")
await researcher.handoff(target_agent=analyst, query="Analyze climate data")

# Visualize the runtime handoff graph
draw_graph(orchestrator, filename="runtime_handoffs")
```

For a complete visualization example, see [Agent Visualization Example](examples/agent_visualization.py)

## Context Preservation

Track conversation context across multiple runs:

```python
from contexa_sdk.observability.context import ConversationContext

# Create a context container
context = ConversationContext()

# Add context to a run
result1 = await agent.run(
    "What's the weather in New York?",
    conversation_context=context
)

# Later, continue with context
result2 = await agent.run(
    "How about tomorrow?",
    conversation_context=context
)
```

## Agent Introspection

Inspect agent internals for debugging:

```python
from contexa_sdk.observability.introspection import AgentIntrospector

# Create an introspector
introspector = AgentIntrospector(agent)

# Get agent state
state = introspector.get_state()

# Get execution graph
graph = introspector.get_execution_graph()

# Print detailed stats
introspector.print_stats()
```

## Examples

For complete examples of observability integration, see:
- [Basic Observability Example](examples/observability_example.py)
- [Advanced Tracing Example](examples/tracing_example.py)
- [Dashboard Setup Example](examples/monitoring_dashboard_example.py) 