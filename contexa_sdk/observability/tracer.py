"""Tracing module for Contexa SDK."""

import os
import time
import uuid
import json
import functools
import threading
import contextvars
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, cast

# Import logger
from contexa_sdk.observability.logger import get_logger

# Create a logger for this module
logger = get_logger(__name__)

# Context variables for trace and span propagation
current_trace_id = contextvars.ContextVar("current_trace_id", default=None)
current_span_id = contextvars.ContextVar("current_span_id", default=None)
current_span = contextvars.ContextVar("current_span", default=None)


class SpanKind(str, Enum):
    """Kind of span in a trace."""
    
    INTERNAL = "internal"
    CLIENT = "client"
    SERVER = "server"
    PRODUCER = "producer"
    CONSUMER = "consumer"
    AGENT = "agent"
    TOOL = "tool"
    MODEL = "model"
    HANDOFF = "handoff"


class SpanStatus(str, Enum):
    """Status of a span."""
    
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


class Span:
    """Representation of a span in a distributed trace."""
    
    def __init__(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent_span_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        start_time: Optional[float] = None,
    ):
        """Initialize a span.
        
        Args:
            name: Name of the span
            kind: Kind of span
            parent_span_id: ID of the parent span
            trace_id: ID of the trace
            start_time: Start time of the span (if not provided, set to current time)
        """
        self.name = name
        self.kind = kind
        self.span_id = str(uuid.uuid4())
        self.trace_id = trace_id or current_trace_id.get() or str(uuid.uuid4())
        self.parent_span_id = parent_span_id or current_span_id.get()
        self.start_time = start_time or time.time()
        self.end_time: Optional[float] = None
        self.status = SpanStatus.UNSET
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []
        self._saved = False
        
        # Save current context before setting new context
        self._token_trace_id = current_trace_id.set(self.trace_id)
        self._token_span_id = current_span_id.set(self.span_id)
        self._token_span = current_span.set(self)
    
    def __enter__(self) -> "Span":
        """Enter the span context.
        
        Returns:
            Self, for use in context managers
        """
        # Context is already set in __init__
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the span context.
        
        Args:
            exc_type: Exception type, if any
            exc_val: Exception value, if any
            exc_tb: Exception traceback, if any
        """
        # End the span
        if exc_type is not None:
            self.record_exception(exc_val)
            self.set_status(SpanStatus.ERROR)
        self.end()
        
        # Restore the previous context
        current_trace_id.reset(self._token_trace_id)
        current_span_id.reset(self._token_span_id)
        current_span.reset(self._token_span)
    
    def end(self, end_time: Optional[float] = None) -> None:
        """End the span.
        
        Args:
            end_time: End time of the span (if not provided, set to current time)
        """
        if self.end_time is not None:
            # Already ended
            return
            
        self.end_time = end_time or time.time()
        self._save()
    
    def set_status(self, status: SpanStatus) -> None:
        """Set the status of the span.
        
        Args:
            status: Status to set
        """
        self.status = status
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the span.
        
        Args:
            key: Attribute key
            value: Attribute value
        """
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span.
        
        Args:
            name: Name of the event
            attributes: Attributes for the event
        """
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })
    
    def record_exception(self, exception: Exception) -> None:
        """Record an exception in the span.
        
        Args:
            exception: Exception to record
        """
        self.add_event(
            name="exception",
            attributes={
                "exception.type": exception.__class__.__name__,
                "exception.message": str(exception),
            },
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the span to a dictionary.
        
        Returns:
            Dictionary representation of the span
        """
        data = {
            "name": self.name,
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "kind": self.kind.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status.value,
            "attributes": self.attributes,
            "events": self.events,
        }
        
        if self.parent_span_id is not None:
            data["parent_span_id"] = self.parent_span_id
            
        return data
    
    def _save(self) -> None:
        """Save the span to storage."""
        if self._saved or self.end_time is None:
            return
            
        self._saved = True
        
        # Get span data as dictionary
        span_data = self.to_dict()
        
        # Save to storage based on environment configuration
        exporter = os.environ.get("CONTEXA_TRACE_EXPORTER", "console").lower()
        
        if exporter == "console":
            # Just log the span
            logger.info(f"Span completed: {self.name}", extra={
                "trace_id": self.trace_id,
                "span_id": self.span_id,
                "span_data": span_data,
            })
        elif exporter == "file":
            # Save to a file
            try:
                trace_dir = os.environ.get("CONTEXA_TRACE_DIR", "./.ctx/traces")
                os.makedirs(trace_dir, exist_ok=True)
                
                filename = f"{trace_dir}/{self.trace_id}.jsonl"
                with open(filename, "a") as f:
                    f.write(json.dumps(span_data) + "\n")
            except Exception as e:
                logger.error(f"Error saving span to file: {str(e)}")
        elif exporter == "otlp":
            # OpenTelemetry protocol export would go here
            # For now, just log that we would export
            logger.info(f"Would export span via OTLP: {self.name}")
        else:
            # Unknown exporter
            logger.warning(f"Unknown trace exporter: {exporter}")


# Type variable for decorated functions
F = TypeVar('F', bound=Callable[..., Any])


def trace(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable[[F], F]:
    """Decorator to trace a function.
    
    Args:
        name: Name of the span (defaults to function name)
        kind: Kind of span
        attributes: Initial attributes for the span
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Use provided name or function name
            span_name = name or f"{func.__module__}.{func.__qualname__}"
            
            # Create span
            with Span(name=span_name, kind=kind) as span:
                # Add initial attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function attributes
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Add first argument if it's self or cls
                if args and (
                    func.__name__ in ("__init__", "__call__")
                    or (hasattr(args[0], "__class__") and func.__module__ == args[0].__class__.__module__)
                ):
                    span.set_attribute("function.target", args[0].__class__.__name__)
                
                try:
                    # Call the function
                    result = func(*args, **kwargs)
                    
                    # If it's a coroutine, we need to trace it as well
                    if asyncio_available and asyncio.iscoroutine(result):
                        async def traced_coro():
                            try:
                                return await result
                            except Exception as e:
                                span.record_exception(e)
                                span.set_status(SpanStatus.ERROR)
                                raise
                            finally:
                                span.end()
                        
                        # Return a new coroutine that will end the span when done
                        return traced_coro()
                    
                    # For normal functions, set status and return
                    span.set_status(SpanStatus.OK)
                    return result
                except Exception as e:
                    # Record exception and re-raise
                    span.record_exception(e)
                    span.set_status(SpanStatus.ERROR)
                    raise
                finally:
                    # End the span if not already ended (for coroutines)
                    if span.end_time is None:
                        span.end()
        
        # For async functions, we need to handle them differently
        if asyncio_available and asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Use provided name or function name
                span_name = name or f"{func.__module__}.{func.__qualname__}"
                
                # Create span
                with Span(name=span_name, kind=kind) as span:
                    # Add initial attributes
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    
                    # Add function attributes
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    # Add first argument if it's self or cls
                    if args and (
                        func.__name__ in ("__init__", "__call__")
                        or (hasattr(args[0], "__class__") and func.__module__ == args[0].__class__.__module__)
                    ):
                        span.set_attribute("function.target", args[0].__class__.__name__)
                    
                    try:
                        # Call the function
                        result = await func(*args, **kwargs)
                        span.set_status(SpanStatus.OK)
                        return result
                    except Exception as e:
                        # Record exception and re-raise
                        span.record_exception(e)
                        span.set_status(SpanStatus.ERROR)
                        raise
            
            return cast(F, async_wrapper)
        
        return cast(F, wrapper)
    
    return decorator


def get_tracer() -> Dict[str, Any]:
    """Get current tracer context.
    
    Returns:
        Dictionary with current trace and span IDs
    """
    return {
        "trace_id": current_trace_id.get(),
        "span_id": current_span_id.get(),
        "current_span": current_span.get(),
    }


# Check if asyncio is available
try:
    import asyncio
    asyncio_available = True
except ImportError:
    asyncio_available = False 