"""Metrics collection and reporting for observability."""

import time
import asyncio
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Callable
from contextlib import contextmanager


class MetricType(str, Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class Metric:
    """A single metric with its metadata."""
    
    def __init__(
        self,
        name: str,
        value: Union[int, float],
        metric_type: MetricType,
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[float] = None,
        description: str = ""
    ):
        """Initialize a metric.
        
        Args:
            name: Name of the metric
            value: Value of the metric
            metric_type: Type of the metric
            tags: Optional tags/dimensions for the metric
            timestamp: Optional timestamp for the metric
            description: Optional description of the metric
        """
        self.name = name
        self.value = value
        self.metric_type = metric_type
        self.tags = tags or {}
        self.timestamp = timestamp or time.time()
        self.description = description


class Counter:
    """A metric that accumulates values."""
    
    def __init__(self, name: str, description: str = "", tags: Optional[Dict[str, str]] = None):
        """Initialize a counter.
        
        Args:
            name: Name of the counter
            description: Description of the counter
            tags: Tags/labels for the counter
        """
        self.name = name
        self.description = description
        self.tags = tags or {}
        self.value = 0
    
    def inc(self, value: Union[int, float] = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment the counter.
        
        Args:
            value: Value to increment by
            tags: Additional tags for this increment
        """
        self.value += value
        
        # Record in global metrics collector if available
        try:
            metrics_collector = _get_metrics_collector()
            if metrics_collector:
                combined_tags = {**self.tags, **(tags or {})}
                metrics_collector.record_counter(self.name, value, combined_tags)
        except Exception:
            # Ignore errors in metrics collection
            pass


class Gauge:
    """A metric that represents a single numerical value."""
    
    def __init__(self, name: str, description: str = "", tags: Optional[Dict[str, str]] = None):
        """Initialize a gauge.
        
        Args:
            name: Name of the gauge
            description: Description of the gauge
            tags: Tags/labels for the gauge
        """
        self.name = name
        self.description = description
        self.tags = tags or {}
        self.value = 0
    
    def set(self, value: Union[int, float], tags: Optional[Dict[str, str]] = None) -> None:
        """Set the gauge value.
        
        Args:
            value: Value to set
            tags: Additional tags for this value
        """
        self.value = value
        
        # Record in global metrics collector if available
        try:
            metrics_collector = _get_metrics_collector()
            if metrics_collector:
                combined_tags = {**self.tags, **(tags or {})}
                metrics_collector.record_gauge(self.name, value, combined_tags)
        except Exception:
            # Ignore errors in metrics collection
            pass
    
    def inc(self, value: Union[int, float] = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment the gauge value.
        
        Args:
            value: Value to increment by
            tags: Additional tags for this increment
        """
        self.value += value
        
        # Record in global metrics collector if available
        try:
            metrics_collector = _get_metrics_collector()
            if metrics_collector:
                combined_tags = {**self.tags, **(tags or {})}
                metrics_collector.record_gauge(self.name, self.value, combined_tags)
        except Exception:
            # Ignore errors in metrics collection
            pass
    
    def dec(self, value: Union[int, float] = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Decrement the gauge value.
        
        Args:
            value: Value to decrement by
            tags: Additional tags for this decrement
        """
        self.value -= value
        
        # Record in global metrics collector if available
        try:
            metrics_collector = _get_metrics_collector()
            if metrics_collector:
                combined_tags = {**self.tags, **(tags or {})}
                metrics_collector.record_gauge(self.name, self.value, combined_tags)
        except Exception:
            # Ignore errors in metrics collection
            pass


class Histogram:
    """A metric that samples observations and counts them in buckets."""
    
    def __init__(self, name: str, description: str = "", tags: Optional[Dict[str, str]] = None):
        """Initialize a histogram.
        
        Args:
            name: Name of the histogram
            description: Description of the histogram
            tags: Tags/labels for the histogram
        """
        self.name = name
        self.description = description
        self.tags = tags or {}
        self.values: List[float] = []
    
    def observe(self, value: Union[int, float], tags: Optional[Dict[str, str]] = None) -> None:
        """Record a value in the histogram.
        
        Args:
            value: Value to record
            tags: Additional tags for this observation
        """
        self.values.append(float(value))
        
        # Record in global metrics collector if available
        try:
            metrics_collector = _get_metrics_collector()
            if metrics_collector:
                combined_tags = {**self.tags, **(tags or {})}
                metrics_collector.record_histogram(self.name, value, combined_tags)
        except Exception:
            # Ignore errors in metrics collection
            pass


class Timer:
    """A utility for measuring execution time."""
    
    def __init__(self, name: str, description: str = "", tags: Optional[Dict[str, str]] = None):
        """Initialize a timer.
        
        Args:
            name: Name of the timer
            description: Description of the timer
            tags: Tags/labels for the timer
        """
        self.name = name
        self.description = description
        self.tags = tags or {}
        self.histogram = Histogram(name, description, tags)
        self.start_time = None
    
    def start(self) -> None:
        """Start the timer."""
        self.start_time = time.time()
    
    def stop(self, tags: Optional[Dict[str, str]] = None) -> float:
        """Stop the timer and record the elapsed time.
        
        Args:
            tags: Additional tags for this observation
            
        Returns:
            Elapsed time in milliseconds
        """
        if self.start_time is None:
            return 0.0
            
        elapsed_time = (time.time() - self.start_time) * 1000.0  # ms
        self.histogram.observe(elapsed_time, tags)
        self.start_time = None
        return elapsed_time
    
    @contextmanager
    def time(self, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing a block of code.
        
        Args:
            tags: Additional tags for this observation
            
        Yields:
            None
        """
        self.start()
        try:
            yield
        finally:
            self.stop(tags)


# Global metric counters and gauges for common uses
agent_requests = Counter("agent.requests.total", "Total number of agent requests")
agent_latency = Histogram("agent.latency.ms", "Agent response latency in milliseconds")
model_tokens = Counter("model.tokens.total", "Total number of tokens used by models")
tool_calls = Counter("tool.calls.total", "Total number of tool calls made")
tool_latency = Histogram("tool.latency.ms", "Tool execution latency in milliseconds")
handoffs = Counter("agent.handoffs.total", "Total number of agent handoffs")
active_agents = Gauge("agent.active", "Number of active agents")


# Global metrics collector
_METRICS_COLLECTOR = None


def _get_metrics_collector():
    """Get the global metrics collector."""
    global _METRICS_COLLECTOR
    if _METRICS_COLLECTOR is None:
        try:
            _METRICS_COLLECTOR = MetricsCollector()
        except Exception:
            # If MetricsCollector can't be instantiated, return None
            pass
    return _METRICS_COLLECTOR


def record_metric(
    name: str,
    value: Union[int, float],
    metric_type: Union[str, MetricType] = MetricType.COUNTER,
    tags: Optional[Dict[str, str]] = None
) -> None:
    """Record a metric using the global metrics collector.
    
    Args:
        name: Name of the metric
        value: Value of the metric
        metric_type: Type of the metric
        tags: Optional tags/dimensions
    """
    collector = _get_metrics_collector()
    if not collector:
        return
        
    # Convert string metric type to enum if needed
    if isinstance(metric_type, str):
        metric_type = MetricType(metric_type.lower())
        
    # Record the metric with the appropriate method
    if metric_type == MetricType.COUNTER:
        collector.record_counter(name, value, tags)
    elif metric_type == MetricType.GAUGE:
        collector.record_gauge(name, value, tags)
    elif metric_type == MetricType.HISTOGRAM:
        collector.record_histogram(name, value, tags)
    elif metric_type == MetricType.SUMMARY:
        # For now, record summaries as histograms
        collector.record_histogram(name, value, tags)


class MetricExporter:
    """Base class for metric exporters.
    
    Metric exporters are responsible for sending metrics to external
    systems like Prometheus, OpenTelemetry, or logging systems.
    """
    
    def __init__(self):
        """Initialize a metric exporter."""
        pass
    
    def export(self, metrics: List[Metric]) -> None:
        """Export metrics to the destination system.
        
        Args:
            metrics: List of metrics to export
        """
        raise NotImplementedError("Subclasses must implement export")
    
    def shutdown(self) -> None:
        """Shutdown the exporter and clean up resources."""
        pass


class ConsoleMetricExporter(MetricExporter):
    """A simple exporter that prints metrics to the console."""
    
    def export(self, metrics: List[Metric]) -> None:
        """Export metrics by printing them to the console.
        
        Args:
            metrics: List of metrics to export
        """
        for metric in metrics:
            tags_str = ", ".join(f"{k}={v}" for k, v in metric.tags.items())
            print(f"{metric.name} ({metric.metric_type.value}): {metric.value} [{tags_str}]")


class MetricsCollector:
    """Collects and manages metrics.
    
    The MetricsCollector provides methods to record different types of metrics
    (counters, gauges, histograms) and export them to one or more destinations.
    """
    
    def __init__(self):
        """Initialize a metrics collector."""
        self.metrics: Dict[str, List[Metric]] = {}
        self.exporters: List[MetricExporter] = []
        self._export_task: Optional[asyncio.Task] = None
        self._is_exporting = False
    
    def add_exporter(self, exporter: MetricExporter) -> None:
        """Add a metric exporter.
        
        Args:
            exporter: The exporter to add
        """
        self.exporters.append(exporter)
    
    def record_counter(
        self, 
        name: str, 
        value: Union[int, float] = 1, 
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a counter metric.
        
        Args:
            name: Name of the counter
            value: Value to increment by
            tags: Optional tags/dimensions
        """
        self._record_metric(name, value, MetricType.COUNTER, tags)
    
    def record_gauge(
        self, 
        name: str, 
        value: Union[int, float], 
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a gauge metric.
        
        Args:
            name: Name of the gauge
            value: Current value
            tags: Optional tags/dimensions
        """
        self._record_metric(name, value, MetricType.GAUGE, tags)
    
    def record_histogram(
        self, 
        name: str, 
        value: Union[int, float], 
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram metric.
        
        Args:
            name: Name of the histogram
            value: Value to record
            tags: Optional tags/dimensions
        """
        self._record_metric(name, value, MetricType.HISTOGRAM, tags)
    
    @contextmanager
    def measure_latency(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Measure the execution time of a block of code.
        
        Args:
            name: Name of the latency metric
            tags: Optional tags/dimensions
            
        Yields:
            None
        """
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000.0
            self.record_histogram(name, latency_ms, tags)
    
    def export_metrics(self) -> None:
        """Export all collected metrics to registered exporters."""
        if not self.exporters:
            return
            
        # Flatten metrics for export
        all_metrics = []
        for metric_list in self.metrics.values():
            all_metrics.extend(metric_list)
            
        # Export to each exporter
        for exporter in self.exporters:
            try:
                exporter.export(all_metrics)
            except Exception:
                # Log the error, but continue with other exporters
                pass
    
    async def start_periodic_export(self, interval_seconds: float = 15.0) -> None:
        """Start periodic export of metrics.
        
        Args:
            interval_seconds: Time between exports in seconds
        """
        if self._is_exporting:
            return
            
        self._is_exporting = True
        self._export_task = asyncio.create_task(self._export_loop(interval_seconds))
    
    async def stop_periodic_export(self) -> None:
        """Stop periodic export of metrics."""
        self._is_exporting = False
        if self._export_task:
            self._export_task.cancel()
            try:
                await self._export_task
            except asyncio.CancelledError:
                pass
            self._export_task = None
    
    def shutdown(self) -> None:
        """Shutdown the metrics collector and all exporters."""
        # Cancel any running export tasks
        if self._export_task and not self._export_task.done():
            self._export_task.cancel()
            
        # Shutdown all exporters
        for exporter in self.exporters:
            exporter.shutdown()
            
        self.exporters = []
    
    def _record_metric(
        self, 
        name: str, 
        value: Union[int, float], 
        metric_type: MetricType, 
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric.
        
        Args:
            name: Name of the metric
            value: Value of the metric
            metric_type: Type of the metric
            tags: Optional tags/dimensions
        """
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {},
            timestamp=time.time()
        )
        
        if name not in self.metrics:
            self.metrics[name] = []
            
        self.metrics[name].append(metric)
    
    async def _export_loop(self, interval_seconds: float) -> None:
        """Background task for periodic metric export."""
        while self._is_exporting:
            try:
                self.export_metrics()
            except Exception:
                # Log the error, but keep the loop running
                pass
                
            await asyncio.sleep(interval_seconds) 