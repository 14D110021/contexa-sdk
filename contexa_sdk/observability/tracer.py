"""Tracing module for distributed request tracing and debugging."""

import time
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable
from contextlib import contextmanager
from enum import Enum, auto
from functools import wraps


class SpanKind(str, Enum):
    """Kinds of spans."""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"
    AGENT = "agent"
    TOOL = "tool"
    HANDOFF = "handoff"
    MODEL = "model"


class SpanStatus(str, Enum):
    """Status codes for spans."""
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


def trace(name: Optional[str] = None, kind: SpanKind = SpanKind.INTERNAL):
    """Decorator for tracing function execution.
    
    Args:
        name: Optional name for the span (uses function name if not provided)
        kind: Kind of span to create
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get the global tracer
            tracer = _get_global_tracer()
            if not tracer:
                return await func(*args, **kwargs)
                
            # Create span name from function name if not provided
            span_name = name or func.__name__
            
            # Create span context
            with tracer.span(span_name, kind=kind) as span:
                # Add function arguments as span attributes
                try:
                    # Add the first argument as 'self' if it's a method
                    if args and hasattr(args[0], '__class__'):
                        span.set_attribute('class', args[0].__class__.__name__)
                    
                    # Add other attributes
                    for i, arg in enumerate(args[1:], 1):
                        if isinstance(arg, (str, int, float, bool)):
                            span.set_attribute(f'arg{i}', str(arg))
                    
                    for k, v in kwargs.items():
                        if isinstance(v, (str, int, float, bool)):
                            span.set_attribute(k, str(v))
                except Exception:
                    # Ignore errors in attribute setting
                    pass
                
                try:
                    # Execute the function
                    result = await func(*args, **kwargs)
                    
                    # Record successful execution
                    span.set_status("ok")
                    return result
                except Exception as e:
                    # Record error
                    span.set_status("error", str(e))
                    span.add_event("exception", {"message": str(e)})
                    raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Get the global tracer
            tracer = _get_global_tracer()
            if not tracer:
                return func(*args, **kwargs)
                
            # Create span name from function name if not provided
            span_name = name or func.__name__
            
            # Create span context
            with tracer.span(span_name, kind=kind) as span:
                # Add function arguments as span attributes
                try:
                    # Add the first argument as 'self' if it's a method
                    if args and hasattr(args[0], '__class__'):
                        span.set_attribute('class', args[0].__class__.__name__)
                    
                    # Add other attributes
                    for i, arg in enumerate(args[1:], 1):
                        if isinstance(arg, (str, int, float, bool)):
                            span.set_attribute(f'arg{i}', str(arg))
                    
                    for k, v in kwargs.items():
                        if isinstance(v, (str, int, float, bool)):
                            span.set_attribute(k, str(v))
                except Exception:
                    # Ignore errors in attribute setting
                    pass
                
                try:
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Record successful execution
                    span.set_status("ok")
                    return result
                except Exception as e:
                    # Record error
                    span.set_status("error", str(e))
                    span.add_event("exception", {"message": str(e)})
                    raise
        
        # Determine if function is async or sync
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


# Global tracer instance
_GLOBAL_TRACER = None


def _get_global_tracer():
    """Get the global tracer instance."""
    global _GLOBAL_TRACER
    if _GLOBAL_TRACER is None:
        _GLOBAL_TRACER = Tracer()
    return _GLOBAL_TRACER


def get_tracer() -> 'Tracer':
    """Get the global tracer instance.
    
    Returns:
        The global tracer instance
    """
    return _get_global_tracer()


class SpanContext:
    """Context for a trace span.
    
    Contains the trace ID and span ID that identify a span in a trace.
    """
    
    def __init__(
        self,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        parent_id: Optional[str] = None
    ):
        """Initialize a span context.
        
        Args:
            trace_id: ID of the trace (generated if not provided)
            span_id: ID of the span (generated if not provided)
            parent_id: ID of the parent span (None for root spans)
        """
        self.trace_id = trace_id or str(uuid.uuid4())
        self.span_id = span_id or str(uuid.uuid4())
        self.parent_id = parent_id


class Span:
    """A single span in a trace.
    
    A span represents a single operation within a trace. Spans can be
    nested to represent a causal relationship between operations.
    """
    
    def __init__(
        self,
        name: str,
        context: SpanContext,
        start_time: Optional[float] = None,
        kind: str = "internal"
    ):
        """Initialize a span.
        
        Args:
            name: Name of the span
            context: Context for the span
            start_time: Start time of the span (now if not provided)
            kind: Kind of span (internal, client, server, producer, consumer)
        """
        self.name = name
        self.context = context
        self.start_time = start_time or time.time()
        self.end_time: Optional[float] = None
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []
        self.status: str = "unset"  # unset, ok, error
        self.status_message: str = ""
        self.kind = kind
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the span.
        
        Args:
            key: Attribute key
            value: Attribute value
        """
        self.attributes[key] = value
    
    def add_event(
        self, 
        name: str, 
        attributes: Optional[Dict[str, Any]] = None, 
        timestamp: Optional[float] = None
    ) -> None:
        """Add an event to the span.
        
        Args:
            name: Name of the event
            attributes: Attributes for the event
            timestamp: Timestamp for the event (now if not provided)
        """
        self.events.append({
            "name": name,
            "attributes": attributes or {},
            "timestamp": timestamp or time.time()
        })
    
    def set_status(self, status: str, message: str = "") -> None:
        """Set the status of the span.
        
        Args:
            status: Status code (ok, error, unset)
            message: Status message
        """
        self.status = status
        self.status_message = message
    
    def end(self, end_time: Optional[float] = None) -> None:
        """End the span.
        
        Args:
            end_time: End time of the span (now if not provided)
        """
        self.end_time = end_time or time.time()
    
    def duration(self) -> float:
        """Get the duration of the span.
        
        Returns:
            Duration in seconds
        """
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time


class TraceOptions:
    """Options for trace configuration."""
    
    def __init__(
        self,
        service_name: str = "contexa-service",
        max_attributes_per_span: int = 100,
        max_events_per_span: int = 100,
        max_links_per_span: int = 100,
        sampling_rate: float = 1.0
    ):
        """Initialize trace options.
        
        Args:
            service_name: Name of the service
            max_attributes_per_span: Maximum number of attributes per span
            max_events_per_span: Maximum number of events per span
            max_links_per_span: Maximum number of links per span
            sampling_rate: Sampling rate (0.0 to 1.0)
        """
        self.service_name = service_name
        self.max_attributes_per_span = max_attributes_per_span
        self.max_events_per_span = max_events_per_span
        self.max_links_per_span = max_links_per_span
        self.sampling_rate = sampling_rate


class TraceExporter:
    """Base class for trace exporters.
    
    Trace exporters are responsible for sending spans to external
    tracing systems like Jaeger, Zipkin, or OpenTelemetry collectors.
    """
    
    def __init__(self):
        """Initialize a trace exporter."""
        pass
    
    def export(self, spans: List[Span]) -> None:
        """Export spans to the destination system.
        
        Args:
            spans: List of spans to export
        """
        raise NotImplementedError("Subclasses must implement export")
    
    def shutdown(self) -> None:
        """Shutdown the exporter and clean up resources."""
        pass


class ConsoleTraceExporter(TraceExporter):
    """A simple exporter that prints spans to the console."""
    
    def export(self, spans: List[Span]) -> None:
        """Export spans by printing them to the console.
        
        Args:
            spans: List of spans to export
        """
        for span in spans:
            duration = span.duration()
            parent = f"parent={span.context.parent_id}" if span.context.parent_id else "root"
            print(f"Span: {span.name} ({parent}) - {duration:.6f}s")
            print(f"  Trace ID: {span.context.trace_id}")
            print(f"  Span ID: {span.context.span_id}")
            print(f"  Status: {span.status}")
            if span.attributes:
                print("  Attributes:")
                for key, value in span.attributes.items():
                    print(f"    {key}: {value}")
            if span.events:
                print("  Events:")
                for event in span.events:
                    print(f"    {event['name']} at {event['timestamp']}")


class Tracer:
    """Creates and manages trace spans.
    
    The Tracer provides methods to create and manage spans for tracing
    requests across distributed systems.
    """
    
    def __init__(self, options: Optional[TraceOptions] = None):
        """Initialize a tracer.
        
        Args:
            options: Trace configuration options
        """
        self.options = options or TraceOptions()
        self.exporters: List[TraceExporter] = []
        self.active_spans: Dict[str, Span] = {}
        self.finished_spans: List[Span] = []
        self._export_task: Optional[asyncio.Task] = None
        self._is_exporting = False
    
    def add_exporter(self, exporter: TraceExporter) -> None:
        """Add a trace exporter.
        
        Args:
            exporter: The exporter to add
        """
        self.exporters.append(exporter)
    
    def start_span(
        self,
        name: str,
        parent: Optional[Union[Span, SpanContext]] = None,
        kind: str = "internal",
        attributes: Optional[Dict[str, Any]] = None
    ) -> Span:
        """Start a new span.
        
        Args:
            name: Name of the span
            parent: Parent span or context
            kind: Kind of span
            attributes: Initial attributes for the span
            
        Returns:
            The new span
        """
        # Create the span context
        if parent is None:
            # Root span
            context = SpanContext()
        elif isinstance(parent, Span):
            # Child of another span
            context = SpanContext(
                trace_id=parent.context.trace_id,
                parent_id=parent.context.span_id
            )
        else:
            # Using an existing context
            context = SpanContext(
                trace_id=parent.trace_id,
                parent_id=parent.span_id
            )
        
        # Create the span
        span = Span(name, context, kind=kind)
        
        # Add initial attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        # Record the active span
        self.active_spans[span.context.span_id] = span
        
        return span
    
    @contextmanager
    def span(
        self,
        name: str,
        parent: Optional[Union[Span, SpanContext]] = None,
        kind: str = "internal",
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Create a span as a context manager.
        
        Args:
            name: Name of the span
            parent: Parent span or context
            kind: Kind of span
            attributes: Initial attributes for the span
            
        Yields:
            The new span
        """
        span = self.start_span(name, parent, kind, attributes)
        try:
            yield span
        except Exception as e:
            span.set_status("error", str(e))
            raise
        finally:
            self.end_span(span)
    
    def end_span(self, span: Span, end_time: Optional[float] = None) -> None:
        """End a span.
        
        Args:
            span: The span to end
            end_time: End time of the span (now if not provided)
        """
        # End the span
        span.end(end_time)
        
        # Remove from active spans
        if span.context.span_id in self.active_spans:
            del self.active_spans[span.context.span_id]
        
        # Add to finished spans
        self.finished_spans.append(span)
        
        # Export if we have any exporters
        if self.exporters:
            for exporter in self.exporters:
                try:
                    exporter.export([span])
                except Exception:
                    # Log the error, but continue with other exporters
                    pass
    
    async def start_periodic_export(self, interval_seconds: float = 15.0) -> None:
        """Start periodic export of spans.
        
        Args:
            interval_seconds: Time between exports in seconds
        """
        if self._is_exporting:
            return
            
        self._is_exporting = True
        self._export_task = asyncio.create_task(self._export_loop(interval_seconds))
    
    async def stop_periodic_export(self) -> None:
        """Stop periodic export of spans."""
        self._is_exporting = False
        if self._export_task:
            self._export_task.cancel()
            try:
                await self._export_task
            except asyncio.CancelledError:
                pass
            self._export_task = None
    
    def shutdown(self) -> None:
        """Shutdown the tracer and all exporters."""
        # Cancel any running export tasks
        if self._export_task and not self._export_task.done():
            self._export_task.cancel()
            
        # Shutdown all exporters
        for exporter in self.exporters:
            exporter.shutdown()
            
        self.exporters = []
    
    def get_active_span(self, span_id: str) -> Optional[Span]:
        """Get an active span by ID.
        
        Args:
            span_id: ID of the span
            
        Returns:
            The span, or None if not found
        """
        return self.active_spans.get(span_id)
    
    def clear_finished_spans(self) -> None:
        """Clear all finished spans."""
        self.finished_spans = []
    
    async def _export_loop(self, interval_seconds: float) -> None:
        """Background task for periodic span export."""
        while self._is_exporting:
            try:
                if self.finished_spans:
                    spans_to_export = self.finished_spans.copy()
                    self.finished_spans = []
                    
                    for exporter in self.exporters:
                        try:
                            exporter.export(spans_to_export)
                        except Exception:
                            # Log the error, but continue with other exporters
                            pass
            except Exception:
                # Log the error, but keep the loop running
                pass
                
            await asyncio.sleep(interval_seconds) 