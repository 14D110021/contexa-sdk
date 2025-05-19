"""Basic tests for observability components."""

import asyncio
import pytest
from contexa_sdk.observability.metrics import MetricsCollector, Metric, MetricType
from contexa_sdk.observability.tracer import Tracer, Span, SpanContext


class TestMetrics:
    """Test the metrics module."""
    
    def test_metrics_collector_init(self):
        """Test that MetricsCollector initializes correctly."""
        collector = MetricsCollector()
        assert collector is not None
        assert isinstance(collector, MetricsCollector)
        assert len(collector.metrics) == 0
        assert len(collector.exporters) == 0
    
    def test_record_counter(self):
        """Test recording a counter metric."""
        collector = MetricsCollector()
        collector.record_counter("test_counter", 1, {"tag1": "value1"})
        
        assert "test_counter" in collector.metrics
        assert len(collector.metrics["test_counter"]) == 1
        
        metric = collector.metrics["test_counter"][0]
        assert metric.name == "test_counter"
        assert metric.value == 1
        assert metric.metric_type == MetricType.COUNTER
        assert metric.tags == {"tag1": "value1"}


class TestTracer:
    """Test the tracer module."""
    
    def test_tracer_init(self):
        """Test that Tracer initializes correctly."""
        tracer = Tracer()
        assert tracer is not None
        assert isinstance(tracer, Tracer)
        assert len(tracer.active_spans) == 0
        assert len(tracer.finished_spans) == 0
        assert len(tracer.exporters) == 0
    
    def test_start_span(self):
        """Test starting a span."""
        tracer = Tracer()
        span = tracer.start_span("test_span")
        
        assert span is not None
        assert isinstance(span, Span)
        assert span.name == "test_span"
        assert span.context.trace_id is not None
        assert span.context.span_id is not None
        assert span.context.parent_id is None
        assert span.end_time is None
        
        # Span should be in active spans
        assert span.context.span_id in tracer.active_spans
        assert tracer.active_spans[span.context.span_id] is span
    
    def test_end_span(self):
        """Test ending a span."""
        tracer = Tracer()
        span = tracer.start_span("test_span")
        tracer.end_span(span)
        
        assert span.end_time is not None
        
        # Span should not be in active spans anymore
        assert span.context.span_id not in tracer.active_spans
        
        # Span should be in finished spans
        assert span in tracer.finished_spans
    
    def test_span_context_manager(self):
        """Test using a span as a context manager."""
        tracer = Tracer()
        
        with tracer.span("test_span") as span:
            assert span is not None
            assert isinstance(span, Span)
            assert span.name == "test_span"
            assert span.end_time is None
            
            # Span should be in active spans
            assert span.context.span_id in tracer.active_spans
        
        # After context manager exits, span should be ended
        assert span.end_time is not None
        assert span.context.span_id not in tracer.active_spans
        assert span in tracer.finished_spans
    
    def test_nested_spans(self):
        """Test nested spans."""
        tracer = Tracer()
        
        with tracer.span("parent_span") as parent:
            # Parent span should be active
            assert parent.context.span_id in tracer.active_spans
            
            with tracer.span("child_span", parent=parent) as child:
                # Both spans should be active
                assert parent.context.span_id in tracer.active_spans
                assert child.context.span_id in tracer.active_spans
                
                # Child should have parent's trace ID and parent's span ID as parent
                assert child.context.trace_id == parent.context.trace_id
                assert child.context.parent_id == parent.context.span_id
            
            # After child context exits, only parent should be active
            assert parent.context.span_id in tracer.active_spans
            assert child.context.span_id not in tracer.active_spans
            assert child in tracer.finished_spans
        
        # After parent context exits, no spans should be active
        assert parent.context.span_id not in tracer.active_spans
        assert parent in tracer.finished_spans 