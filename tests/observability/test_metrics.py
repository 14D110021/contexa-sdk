"""Unit tests for the metrics module."""

import pytest
import unittest.mock as mock
import time
import asyncio
from typing import Dict, Any, List

from contexa_sdk.observability.metrics import (
    MetricsCollector, 
    Metric, 
    MetricType, 
    MetricExporter
)


class MockExporter(MetricExporter):
    """Mock metric exporter for testing."""
    
    def __init__(self):
        """Initialize the mock exporter."""
        self.exported_metrics = []
    
    def export(self, metrics: List[Metric]):
        """Export metrics by storing them in the exported_metrics list."""
        self.exported_metrics.extend(metrics)
    
    def shutdown(self):
        """Mock shutdown method."""
        self.exported_metrics = []


class TestMetricsCollector:
    """Test the MetricsCollector class."""
    
    def test_init(self):
        """Test that MetricsCollector initializes correctly."""
        collector = MetricsCollector()
        assert collector is not None
        assert isinstance(collector, MetricsCollector)
        assert len(collector._metrics) == 0
        assert len(collector._exporters) == 0
    
    def test_record_counter(self):
        """Test recording a counter metric."""
        collector = MetricsCollector()
        
        # Record a counter
        collector.record_counter("test.counter", 1, {"tag1": "value1"})
        
        # Verify the metric was recorded
        assert "test.counter" in collector._metrics
        metric = collector._metrics["test.counter"]
        assert metric.name == "test.counter"
        assert metric.type == MetricType.COUNTER
        assert metric.value == 1
        assert metric.tags == {"tag1": "value1"}
        
        # Record the counter again
        collector.record_counter("test.counter", 2, {"tag1": "value1"})
        
        # Verify the counter was incremented
        assert collector._metrics["test.counter"].value == 3
    
    def test_record_gauge(self):
        """Test recording a gauge metric."""
        collector = MetricsCollector()
        
        # Record a gauge
        collector.record_gauge("test.gauge", 42, {"tag1": "value1"})
        
        # Verify the metric was recorded
        assert "test.gauge" in collector._metrics
        metric = collector._metrics["test.gauge"]
        assert metric.name == "test.gauge"
        assert metric.type == MetricType.GAUGE
        assert metric.value == 42
        assert metric.tags == {"tag1": "value1"}
        
        # Record the gauge again with a different value
        collector.record_gauge("test.gauge", 84, {"tag1": "value1"})
        
        # Verify the gauge was updated (not incremented)
        assert collector._metrics["test.gauge"].value == 84
    
    def test_record_histogram(self):
        """Test recording a histogram metric."""
        collector = MetricsCollector()
        
        # Record a histogram value
        collector.record_histogram("test.histogram", 100, {"tag1": "value1"})
        
        # Verify the metric was recorded
        assert "test.histogram" in collector._metrics
        metric = collector._metrics["test.histogram"]
        assert metric.name == "test.histogram"
        assert metric.type == MetricType.HISTOGRAM
        assert len(metric.value) == 1  # Should contain one value in the distribution
        assert metric.value[0] == 100
        assert metric.tags == {"tag1": "value1"}
        
        # Record another value
        collector.record_histogram("test.histogram", 200, {"tag1": "value1"})
        
        # Verify the value was added to the distribution
        assert len(collector._metrics["test.histogram"].value) == 2
        assert 100 in collector._metrics["test.histogram"].value
        assert 200 in collector._metrics["test.histogram"].value
    
    def test_add_exporter(self):
        """Test adding a metric exporter."""
        collector = MetricsCollector()
        exporter = MockExporter()
        
        # Add the exporter
        collector.add_exporter(exporter)
        
        # Verify the exporter was added
        assert exporter in collector._exporters
    
    def test_export_metrics(self):
        """Test exporting metrics to exporters."""
        collector = MetricsCollector()
        exporter = MockExporter()
        collector.add_exporter(exporter)
        
        # Record some metrics
        collector.record_counter("test.counter", 1, {"tag1": "value1"})
        collector.record_gauge("test.gauge", 42, {"tag2": "value2"})
        
        # Export the metrics
        collector.export_metrics()
        
        # Verify the metrics were exported
        assert len(exporter.exported_metrics) == 2
        metric_names = [m.name for m in exporter.exported_metrics]
        assert "test.counter" in metric_names
        assert "test.gauge" in metric_names
    
    @pytest.mark.asyncio
    async def test_measure_latency(self):
        """Test measuring latency with the context manager."""
        collector = MetricsCollector()
        
        # Use the context manager to measure latency
        with collector.measure_latency("test.latency", {"tag1": "value1"}):
            # Simulate some work
            await asyncio.sleep(0.1)
        
        # Verify the metric was recorded
        assert "test.latency" in collector._metrics
        metric = collector._metrics["test.latency"]
        assert metric.name == "test.latency"
        assert metric.type == MetricType.HISTOGRAM
        assert len(metric.value) == 1  # Should contain one latency measurement
        # The value should be around 100ms, but allow some tolerance
        assert 50 <= metric.value[0] <= 150
        assert metric.tags == {"tag1": "value1"}
    
    def test_record_with_different_tags(self):
        """Test recording metrics with different tag sets."""
        collector = MetricsCollector()
        
        # Record a counter with one set of tags
        collector.record_counter("test.counter", 1, {"env": "prod"})
        
        # Record the same counter with a different set of tags
        collector.record_counter("test.counter", 2, {"env": "dev"})
        
        # Verify we have two separate metrics for the same name but different tags
        assert len(collector._metrics) == 2
        assert "test.counter||env=prod" in collector._metrics
        assert "test.counter||env=dev" in collector._metrics
    
    def test_get_metrics(self):
        """Test getting all metrics."""
        collector = MetricsCollector()
        
        # Record some metrics
        collector.record_counter("test.counter", 1, {"tag1": "value1"})
        collector.record_gauge("test.gauge", 42, {"tag2": "value2"})
        
        # Get all metrics
        metrics = collector.get_metrics()
        
        # Verify we got all metrics
        assert len(metrics) == 2
        metric_names = [m.name for m in metrics]
        assert "test.counter" in metric_names
        assert "test.gauge" in metric_names
    
    def test_reset_metrics(self):
        """Test resetting all metrics."""
        collector = MetricsCollector()
        
        # Record some metrics
        collector.record_counter("test.counter", 1, {"tag1": "value1"})
        collector.record_gauge("test.gauge", 42, {"tag2": "value2"})
        
        # Reset the metrics
        collector.reset_metrics()
        
        # Verify all metrics were reset
        assert len(collector._metrics) == 0 