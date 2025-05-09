#!/usr/bin/env python
"""Example demonstrating observability features in the Contexa SDK."""

import os
import asyncio
import argparse
from typing import Dict, List, Any, Optional

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import BaseTool, ToolResult
from contexa_sdk.core.memory import ContexaMemory
from contexa_sdk.core.config import ContexaConfig
from contexa_sdk.core.model import ContexaModel

# Import observability modules
from contexa_sdk.observability import (
    get_logger,
    trace, 
    Span, 
    SpanKind, 
    record_metric,
)
from contexa_sdk.observability.metrics import (
    Timer,
    counter,
    gauge,
    histogram,
    start_metrics_collection,
    stop_metrics_collection,
)

# Create a logger for this example
logger = get_logger(__name__)

# Define custom metrics for this example
example_operations = counter(
    "example_operations_total",
    "Total operations performed in the example",
    ["operation_type"],
)

example_processing_time = histogram(
    "example_processing_time_seconds",
    "Time taken to process requests in the example",
    [0.001, 0.01, 0.1, 0.5, 1.0, 5.0],
    ["operation_type"],
)


# Define a simple tool for the example
class SearchTool(BaseTool):
    """Tool for searching information."""
    
    name = "search"
    description = "Search for information on a topic"
    
    def __init__(self):
        """Initialize the search tool."""
        parameters = {
            "query": {
                "type": "string",
                "description": "The search query",
                "required": True
            }
        }
        super().__init__(parameters=parameters)
    
    @trace(kind=SpanKind.TOOL)
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the search tool."""
        query = kwargs.get("query", "")
        
        # Log the execution
        logger.info(
            f"Executing search tool with query: {query}",
            extra={
                "tool": "search",
                "query": query,
            }
        )
        
        # Record metric
        example_operations.inc(1, operation_type="search_tool")
        
        # Simulate search with a timer
        with Timer(example_processing_time, operation_type="search_tool"):
            # Simulate some processing time
            await asyncio.sleep(0.1)
            
            # Simulate search results
            search_data = {
                "query": query,
                "results": [
                    {"title": f"Result 1 for {query}", "snippet": "This is the first result."},
                    {"title": f"Result 2 for {query}", "snippet": "This is the second result."},
                    {"title": f"Result 3 for {query}", "snippet": "This is the third result."},
                ]
            }
            
            # Create a result message
            result_text = f"Here are some results for '{query}':\n\n"
            for i, result in enumerate(search_data["results"], 1):
                result_text += f"{i}. {result['title']}\n   {result['snippet']}\n\n"
        
        return ToolResult(
            result=result_text,
            raw_data=search_data
        )


class CalculatorTool(BaseTool):
    """Tool for performing calculations."""
    
    name = "calculator"
    description = "Perform a calculation"
    
    def __init__(self):
        """Initialize the calculator tool."""
        parameters = {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate",
                "required": True
            }
        }
        super().__init__(parameters=parameters)
    
    @trace(kind=SpanKind.TOOL)
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the calculator tool."""
        expression = kwargs.get("expression", "")
        
        # Log the execution
        logger.info(
            f"Executing calculator tool with expression: {expression}",
            extra={
                "tool": "calculator",
                "expression": expression,
            }
        )
        
        # Record metric
        example_operations.inc(1, operation_type="calculator_tool")
        
        # Start a timer
        with Timer(example_processing_time, operation_type="calculator_tool"):
            try:
                # This is unsafe for production but ok for an example
                result = eval(expression)
                
                # Prepare result
                result_text = f"The result of {expression} is {result}"
                result_data = {
                    "expression": expression,
                    "result": result
                }
                
                return ToolResult(
                    result=result_text,
                    raw_data=result_data
                )
            except Exception as e:
                # Log error
                logger.error(
                    f"Error evaluating expression: {str(e)}",
                    extra={
                        "tool": "calculator",
                        "expression": expression,
                        "error": str(e),
                    }
                )
                
                return ToolResult(
                    result=f"Error evaluating expression: {str(e)}",
                    raw_data={
                        "expression": expression,
                        "error": str(e)
                    }
                )


# Example model that always returns a fixed response
class DummyModel(ContexaModel):
    """Dummy model for demonstration purposes."""
    
    def __init__(self, response_type: str = "simple"):
        """Initialize the dummy model.
        
        Args:
            response_type: Type of response to generate (simple, tool, error)
        """
        super().__init__(
            model_name="dummy-model",
            provider="dummy",
            config=ContexaConfig(),
        )
        self.response_type = response_type
    
    @trace(kind=SpanKind.MODEL)
    async def generate(self, messages):
        """Generate a response from the dummy model."""
        
        # Log and record metrics
        logger.info(
            f"Generating response from dummy model",
            extra={
                "model": "dummy-model",
                "response_type": self.response_type,
                "message_count": len(messages),
            }
        )
        
        # Record token usage - even though this is a dummy model
        # we track tokens to demonstrate metrics
        input_tokens = sum(len(m.content.split()) for m in messages if m.content)
        record_metric(
            "counter",
            "model_tokens_total",
            input_tokens,
            labels={
                "model_name": "dummy-model",
                "provider": "dummy",
                "type": "input"
            }
        )
        
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        # Generate a response based on the response type
        if self.response_type == "simple":
            content = "This is a simple response from the dummy model."
        elif self.response_type == "tool":
            content = """I'll search for information on that topic.

```tool
{"name": "search", "parameters": {"query": "artificial intelligence"}}
```
"""
        elif self.response_type == "calculation":
            content = """I'll calculate that for you.

```tool
{"name": "calculator", "parameters": {"expression": "42 + 7 * 3"}}
```
"""
        elif self.response_type == "error":
            # Simulate an error
            raise ValueError("Simulated error from dummy model")
        else:
            content = f"Unknown response type: {self.response_type}"
        
        # Simulate token usage for the output
        output_tokens = len(content.split())
        record_metric(
            "counter",
            "model_tokens_total",
            output_tokens,
            labels={
                "model_name": "dummy-model",
                "provider": "dummy",
                "type": "output"
            }
        )
        
        # Create a model message
        from contexa_sdk.core.model import ModelMessage
        return ModelMessage(role="assistant", content=content)


@trace(kind=SpanKind.INTERNAL)
async def create_example_agent(response_type: str = "simple") -> ContexaAgent:
    """Create an example agent with observability features.
    
    Args:
        response_type: Type of response for the dummy model to generate
        
    Returns:
        A ContexaAgent
    """
    logger.info(f"Creating example agent with response type: {response_type}")
    
    # Record the operation
    example_operations.inc(1, operation_type="create_agent")
    
    # Create tools
    tools = [SearchTool(), CalculatorTool()]
    
    # Create model
    model = DummyModel(response_type=response_type)
    
    # Create agent
    agent = ContexaAgent(
        name="Observability Demo Agent",
        description="An agent that demonstrates observability features",
        tools=tools,
        model=model,
        config=ContexaConfig(),
        agent_id="obs-demo-agent-123",
    )
    
    return agent


@trace(kind=SpanKind.AGENT)
async def run_example(
    query: str,
    response_type: str = "simple",
    run_count: int = 1
) -> None:
    """Run the observability example.
    
    Args:
        query: Query to send to the agent
        response_type: Type of response for the dummy model to generate
        run_count: Number of times to run the agent
    """
    # Create agent
    agent = await create_example_agent(response_type)
    
    # Run the agent multiple times
    for i in range(run_count):
        # Log the run
        logger.info(
            f"Running agent (iteration {i+1}/{run_count})",
            extra={
                "agent_id": agent.agent_id,
                "query": query,
                "iteration": i+1,
                "run_count": run_count,
            }
        )
        
        # Add a span for this run
        with Span(name=f"agent_run_{i+1}", kind=SpanKind.AGENT) as span:
            span.set_attribute("agent.id", agent.agent_id)
            span.set_attribute("agent.name", agent.name)
            span.set_attribute("query", query)
            span.set_attribute("iteration", i+1)
            
            try:
                # Run the agent
                with Timer(example_processing_time, operation_type="agent_run"):
                    response = await agent.run(query)
                
                # Log the response
                logger.info(
                    f"Agent response (iteration {i+1}/{run_count})",
                    extra={
                        "agent_id": agent.agent_id,
                        "response": response,
                        "iteration": i+1,
                        "run_count": run_count,
                    }
                )
                
                span.set_attribute("response", response)
                
            except Exception as e:
                # Log the error
                logger.error(
                    f"Error running agent (iteration {i+1}/{run_count}): {str(e)}",
                    extra={
                        "agent_id": agent.agent_id,
                        "error": str(e),
                        "iteration": i+1,
                        "run_count": run_count,
                    }
                )
                span.set_attribute("error", str(e))


async def main():
    """Run the observability example."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Contexa SDK Observability Example")
    parser.add_argument(
        "--query",
        type=str,
        default="Tell me about artificial intelligence",
        help="Query to send to the agent",
    )
    parser.add_argument(
        "--response-type",
        type=str,
        choices=["simple", "tool", "calculation", "error"],
        default="tool",
        help="Type of response for the model to generate",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of times to run the agent",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Log level",
    )
    parser.add_argument(
        "--log-format",
        type=str,
        choices=["text", "JSON"],
        default="text",
        help="Log format",
    )
    parser.add_argument(
        "--trace-exporter",
        type=str,
        choices=["console", "file", "otlp"],
        default="console",
        help="Trace exporter",
    )
    parser.add_argument(
        "--metrics-exporter",
        type=str,
        choices=["console", "file", "prometheus"],
        default="console",
        help="Metrics exporter",
    )
    args = parser.parse_args()
    
    # Set environment variables for observability
    os.environ["CONTEXA_LOG_LEVEL"] = args.log_level
    os.environ["CONTEXA_LOG_FORMAT"] = args.log_format
    os.environ["CONTEXA_TRACE_EXPORTER"] = args.trace_exporter
    os.environ["CONTEXA_METRICS_EXPORTER"] = args.metrics_exporter
    
    # Set up metrics collection
    start_metrics_collection()
    
    # Log the start of the example
    logger.info(
        "Starting observability example",
        extra={
            "query": args.query,
            "response_type": args.response_type,
            "runs": args.runs,
            "log_level": args.log_level,
            "log_format": args.log_format,
            "trace_exporter": args.trace_exporter,
            "metrics_exporter": args.metrics_exporter,
        }
    )
    
    # Create a top-level span for the entire example
    with Span(name="observability_example", kind=SpanKind.INTERNAL) as span:
        span.set_attribute("query", args.query)
        span.set_attribute("response_type", args.response_type)
        span.set_attribute("runs", args.runs)
        
        try:
            # Run the example
            await run_example(
                query=args.query,
                response_type=args.response_type,
                run_count=args.runs,
            )
            
            span.set_attribute("status", "success")
            
        except Exception as e:
            # Log the error
            logger.error(
                f"Error running example: {str(e)}",
                extra={
                    "error": str(e),
                }
            )
            span.set_attribute("status", "error")
            span.set_attribute("error", str(e))
    
    # Stop metrics collection
    stop_metrics_collection()
    
    # Log the end of the example
    logger.info("Observability example completed")


if __name__ == "__main__":
    asyncio.run(main()) 