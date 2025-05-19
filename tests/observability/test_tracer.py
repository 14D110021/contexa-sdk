"""Unit tests for the tracer module."""

import pytest
import unittest.mock as mock
import asyncio
from typing import Dict, Any, List, Optional

from contexa_sdk.observability.tracer import (
    Tracer,
    Span,
    SpanContext,
    TraceExporter,
    TraceOptions
)


class MockTraceExporter(TraceExporter):
    """Mock trace exporter for testing."""
    
    def __init__(self):
        """Initialize the mock exporter."""
        self.exported_spans = []
    
    def export(self, spans: List[Span]):
        """Export spans by storing them in the exported_spans list."""
        self.exported_spans.extend(spans)
    
    def shutdown(self):
        """Mock shutdown method."""
        self.exported_spans = []


class TestTracer:
    """Test the Tracer class."""
    
    def test_init(self):
        """Test that Tracer initializes correctly."""
        tracer = Tracer()
        assert tracer is not None
        assert isinstance(tracer, Tracer)
        assert len(tracer._spans) == 0
        assert len(tracer._exporters) == 0
    
    def test_trace_options_init(self):
        """Test that TraceOptions initializes correctly."""
        options = TraceOptions(
            service_name="test-service",
            environment="test",
            enable_sampling=True,
            sampling_rate=0.5
        )
        assert options.service_name == "test-service"
        assert options.environment == "test"
        assert options.enable_sampling is True
        assert options.sampling_rate == 0.5
    
    def test_start_span(self):
        """Test starting a span."""
        tracer = Tracer()
        
        # Start a span
        with tracer.start_span("test-span") as span:
            # Verify the span is created correctly
            assert span is not None
            assert isinstance(span, Span)
            assert span.name == "test-span"
            assert span.parent_id is None
            assert span.status == "ok"
            assert span.start_time > 0
            assert span.end_time is None
            
            # Set some attributes
            span.set_attribute("key1", "value1")
            span.set_attribute("key2", 42)
            
            # Verify the attributes were set
            assert span.attributes["key1"] == "value1"
            assert span.attributes["key2"] == 42
        
        # Verify the span was ended
        assert span.end_time is not None
        assert span.end_time >= span.start_time
    
    def test_nested_spans(self):
        """Test creating nested spans."""
        tracer = Tracer()
        
        # Start a parent span
        with tracer.start_span("parent-span") as parent:
            # Start a child span
            with tracer.start_span("child-span", parent=parent) as child:
                # Verify the child span is linked to the parent
                assert child.parent_id == parent.span_id
                
                # Start a grandchild span
                with tracer.start_span("grandchild-span", parent=child) as grandchild:
                    # Verify the grandchild span is linked to the child
                    assert grandchild.parent_id == child.span_id
    
    def test_add_exporter(self):
        """Test adding a trace exporter."""
        tracer = Tracer()
        exporter = MockTraceExporter()
        
        # Add the exporter
        tracer.add_exporter(exporter)
        
        # Verify the exporter was added
        assert exporter in tracer._exporters
    
    def test_export_spans(self):
        """Test exporting spans to exporters."""
        tracer = Tracer()
        exporter = MockTraceExporter()
        tracer.add_exporter(exporter)
        
        # Create some spans
        with tracer.start_span("span1"):
            pass
        
        with tracer.start_span("span2"):
            pass
        
        # Export the spans
        tracer.export_spans()
        
        # Verify the spans were exported
        assert len(exporter.exported_spans) == 2
        span_names = [s.name for s in exporter.exported_spans]
        assert "span1" in span_names
        assert "span2" in span_names
    
    def test_span_error(self):
        """Test recording an error in a span."""
        tracer = Tracer()
        
        try:
            # Start a span
            with tracer.start_span("error-span") as span:
                # Simulate an error
                raise ValueError("Test error")
        except ValueError:
            # Verify the span recorded the error
            assert span.status == "error"
            assert "error" in span.attributes
            assert "Test error" in span.attributes["error"]
    
    def test_current_span(self):
        """Test getting the current span."""
        tracer = Tracer()
        
        # Initially, there should be no current span
        assert tracer.current_span is None
        
        # Start a span
        with tracer.start_span("span1") as span1:
            # Now the current span should be span1
            assert tracer.current_span == span1
            
            # Start a nested span
            with tracer.start_span("span2") as span2:
                # Now the current span should be span2
                assert tracer.current_span == span2
            
            # After span2 ends, current span should be span1 again
            assert tracer.current_span == span1
        
        # After all spans end, there should be no current span
        assert tracer.current_span is None
    
    def test_span_context(self):
        """Test creating and using a span context."""
        tracer = Tracer()
        
        # Create a span context
        context = SpanContext(
            trace_id="trace-123",
            span_id="span-123",
            is_remote=False
        )
        
        # Start a span with this context
        with tracer.start_span("context-span", context=context) as span:
            # Verify the span uses the provided context
            assert span.trace_id == "trace-123"
            assert span.parent_id == "span-123"
    
    def test_trace_across_async_operations(self):
        """Test tracing across asynchronous operations."""
        tracer = Tracer()
        
        async def async_operation():
            # Get the current span from the tracer
            parent_span = tracer.current_span
            
            # Create a child span
            with tracer.start_span("async-span", parent=parent_span) as child_span:
                # Do some async work
                await asyncio.sleep(0.1)
                return "result"
        
        # Run the async operation inside a parent span
        with tracer.start_span("parent-span") as parent_span:
            # Run the async operation
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(async_operation())
            
            # Verify the result
            assert result == "result"
            
            # Verify the child span was properly linked to the parent
            child_spans = [s for s in tracer._spans if s.parent_id == parent_span.span_id]
            assert len(child_spans) == 1
            assert child_spans[0].name == "async-span" 