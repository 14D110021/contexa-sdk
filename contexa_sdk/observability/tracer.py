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
    """Creates and manages trace spans for distributed request tracing.
    
    The Tracer is responsible for creating and tracking spans across distributed
    systems, enabling observability into request flows through multiple components.
    It provides functionality for:
    
    1. Creating spans to represent operations or processing steps
    2. Building parent-child relationships between spans to model causality
    3. Adding attributes, events, and status information to spans
    4. Exporting span data to observability systems
    5. Managing the lifecycle of spans
    
    This implementation supports both manual span creation and context manager-based
    span management, with support for distributed tracing across different services
    and integration with various tracing backends through exporters.
    
    Attributes:
        options: Configuration options for the tracer
        exporters: List of registered trace exporters
        active_spans: Dictionary of currently active spans by span ID
        finished_spans: List of completed spans waiting for export
        _export_task: Background task for periodic span export
        _is_exporting: Flag indicating if periodic export is active
    """
    
    def __init__(self, options: Optional[TraceOptions] = None):
        """Initialize a tracer with configuration options.
        
        Creates a new tracer instance with the specified configuration options
        or default options if none are provided. The tracer starts with no
        exporters and no active spans.
        
        Args:
            options: Optional configuration options controlling tracing behavior
                such as service name, sampling rate, and limits on span attributes.
                If not provided, default options are used.
        """
        self.options = options or TraceOptions()
        self.exporters: List[TraceExporter] = []
        self.active_spans: Dict[str, Span] = {}
        self.finished_spans: List[Span] = []
        self._export_task: Optional[asyncio.Task] = None
        self._is_exporting = False
    
    def add_exporter(self, exporter: TraceExporter) -> None:
        """Add a trace exporter to receive completed spans.
        
        Exporters are responsible for sending spans to external tracing systems
        such as Jaeger, Zipkin, OpenTelemetry collectors, or logging systems.
        Multiple exporters can be added to send spans to different destinations.
        
        Args:
            exporter: The exporter instance to add. Must implement the
                TraceExporter interface with an export() method.
                
        Example:
            ```python
            tracer = Tracer()
            tracer.add_exporter(ConsoleTraceExporter())
            tracer.add_exporter(OTelTraceExporter("http://collector:4317"))
            ```
        """
        self.exporters.append(exporter)
    
    def start_span(
        self,
        name: str,
        parent: Optional[Union[Span, SpanContext]] = None,
        kind: str = "internal",
        attributes: Optional[Dict[str, Any]] = None
    ) -> Span:
        """Start a new span to track an operation.
        
        Creates a new span representing an operation or processing step. The span
        can be a root span (no parent) or a child of another span to represent
        a causal relationship. The returned span must be ended with end_span()
        when the operation completes.
        
        Args:
            name: Human-readable name for the operation (e.g., "process_request")
            parent: Optional parent span or span context to establish a causal
                relationship. If None, creates a root span with a new trace ID.
            kind: Type of span, indicating the role in the request flow. Valid values
                include "internal", "server", "client", "producer", "consumer", 
                "agent", "tool", "handoff", and "model".
            attributes: Optional initial attributes to add to the span for additional
                context, such as operation parameters or metadata.
            
        Returns:
            A new Span object representing the started operation
            
        Example:
            ```python
            # Create a root span
            root_span = tracer.start_span("process_request", kind="server")
            
            # Create a child span
            child_span = tracer.start_span("fetch_data", parent=root_span, kind="client",
                                         attributes={"database": "users"})
            
            # Don't forget to end spans when operations complete
            tracer.end_span(child_span)
            tracer.end_span(root_span)
            ```
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
        """Create and automatically manage a span using a context manager.
        
        This is the preferred way to create spans as it ensures they are properly
        ended even if exceptions occur. The span is automatically started when
        entering the context and ended when exiting.
        
        Args:
            name: Human-readable name for the operation (e.g., "process_request")
            parent: Optional parent span or span context to establish a causal
                relationship. If None, creates a root span with a new trace ID.
            kind: Type of span, indicating the role in the request flow. Valid values
                include "internal", "server", "client", "producer", "consumer", 
                "agent", "tool", "handoff", and "model".
            attributes: Optional initial attributes to add to the span
            
        Yields:
            An active Span object that can be used to add attributes, events, or
            set status information during the operation
            
        Example:
            ```python
            # Using context manager for automatic span management
            with tracer.span("process_request", kind="server") as root_span:
                # Do some work
                root_span.set_attribute("user_id", "123")
                
                # Nested span using parent
                with tracer.span("fetch_data", parent=root_span, kind="client") as child_span:
                    # Do more work
                    child_span.add_event("cache_miss")
                    data = fetch_data_from_db()
            # Both spans are automatically ended when their contexts exit
            ```
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
        """End a span, marking the operation as complete.
        
        This method finalizes a span by setting its end time, removing it from
        active spans, and adding it to finished spans for export. If exporters
        are registered, the span is immediately exported.
        
        Args:
            span: The span to end, previously created with start_span()
            end_time: Optional explicit end time as a timestamp (seconds since epoch).
                If not provided, the current time is used.
                
        Note:
            Spans created with the span() context manager are automatically ended
            and don't need to be ended manually.
            
        Example:
            ```python
            span = tracer.start_span("process_data")
            try:
                # Do some work
                process_data()
                span.set_status("ok")
            except Exception as e:
                span.set_status("error", str(e))
                raise
            finally:
                tracer.end_span(span)
            ```
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
        """Start periodic export of finished spans at specified intervals.
        
        Begins an asynchronous task that exports spans at regular intervals.
        This is useful for batching span exports to reduce overhead and network
        traffic, especially in high-throughput applications.
        
        Args:
            interval_seconds: Time between exports in seconds (default: 15.0)
                
        Note:
            If periodic export is already running, this method is a no-op.
            The task runs until stop_periodic_export() is called or the
            application shuts down.
            
        Example:
            ```python
            # Start exporting spans every 5 seconds
            await tracer.start_periodic_export(5.0)
            ```
        """
        if self._is_exporting:
            return
            
        self._is_exporting = True
        self._export_task = asyncio.create_task(self._export_loop(interval_seconds))
    
    async def stop_periodic_export(self) -> None:
        """Stop periodic export of spans.
        
        Cancels the background task that periodically exports spans.
        Any spans collected after this call will not be automatically
        exported until start_periodic_export() is called again.
        
        This method is asynchronous and waits for the export task to
        be fully cancelled before returning.
        
        Example:
            ```python
            # Stop the periodic export
            await tracer.stop_periodic_export()
            ```
        """
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