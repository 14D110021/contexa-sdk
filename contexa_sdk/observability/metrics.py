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
    """Collects, manages, and exports metrics for observability.
    
    The MetricsCollector is the central component of the metrics system, providing:
    
    1. Methods to record different types of metrics (counters, gauges, histograms)
    2. Tagging/labeling capabilities for metric dimensions
    3. Integration with multiple metric exporters for different destinations
    4. Automatic periodic export of metrics to registered exporters
    5. Utilities for measuring latency of operations
    
    The collector maintains metrics in memory and can export them on demand or
    periodically to configured exporters. Multiple exporters can be registered
    to send metrics to different observability systems simultaneously.
    
    This class is designed to be thread-safe and can be used across async and
    synchronous code contexts.
    
    Attributes:
        metrics: Dictionary mapping metric names to lists of recorded metrics
        exporters: List of registered metric exporters
        _export_task: Background task for periodic metric export
        _is_exporting: Flag indicating if periodic export is active
    """
    
    def __init__(self):
        """Initialize a metrics collector with empty metrics and exporters lists."""
        self.metrics: Dict[str, List[Metric]] = {}
        self.exporters: List[MetricExporter] = []
        self._export_task: Optional[asyncio.Task] = None
        self._is_exporting = False
    
    def add_exporter(self, exporter: MetricExporter) -> None:
        """Add a metric exporter to receive collected metrics.
        
        Exporters are responsible for sending metrics to external systems such as
        Prometheus, OpenTelemetry collectors, logging systems, or cloud monitoring
        services. Multiple exporters can be added to send metrics to different
        destinations simultaneously.
        
        Args:
            exporter: The exporter instance to add. Must implement the
                MetricExporter interface with an export() method.
        """
        self.exporters.append(exporter)
    
    def record_counter(
        self, 
        name: str, 
        value: Union[int, float] = 1, 
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a counter metric that tracks cumulative values.
        
        Counters are monotonically increasing values used for measuring things
        like the number of requests, errors, or operations performed. They
        should only increase or be reset to zero.
        
        Args:
            name: Name of the counter metric (e.g., "agent.requests.total")
            value: Amount to increment the counter by (default: 1)
            tags: Optional dictionary of tag key/value pairs for adding
                dimensions to the metric (e.g., {"agent_id": "abc123"})
                
        Example:
            ```python
            # Record a request with agent type dimension
            metrics.record_counter("agent.requests.total", 1, {"agent_type": "search"})
            ```
        """
        self._record_metric(name, value, MetricType.COUNTER, tags)
    
    def record_gauge(
        self, 
        name: str, 
        value: Union[int, float], 
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a gauge metric that represents a current value.
        
        Gauges are metrics that can increase and decrease, representing
        current values like memory usage, active connections, or queue depth.
        
        Args:
            name: Name of the gauge metric (e.g., "agent.memory.mb")
            value: Current value of the gauge
            tags: Optional dictionary of tag key/value pairs for adding
                dimensions to the metric (e.g., {"agent_id": "abc123"})
                
        Example:
            ```python
            # Record current memory usage for an agent
            metrics.record_gauge("agent.memory.mb", 128.5, {"agent_id": "abc123"})
            ```
        """
        self._record_metric(name, value, MetricType.GAUGE, tags)
    
    def record_histogram(
        self, 
        name: str, 
        value: Union[int, float], 
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram metric that tracks value distributions.
        
        Histograms track the distribution of values, useful for measuring
        things like response times, payload sizes, or other values where
        the distribution matters. They typically generate percentiles,
        averages, and counts.
        
        Args:
            name: Name of the histogram metric (e.g., "agent.latency.ms")
            value: Value to record in the histogram
            tags: Optional dictionary of tag key/value pairs for adding
                dimensions to the metric (e.g., {"operation": "search"})
                
        Example:
            ```python
            # Record response time for a query
            metrics.record_histogram("agent.latency.ms", 45.2, {"query_type": "search"})
            ```
        """
        self._record_metric(name, value, MetricType.HISTOGRAM, tags)
    
    @contextmanager
    def measure_latency(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Measure the execution time of a block of code as a histogram metric.
        
        A context manager that automatically times the execution of the code
        block and records it as a histogram metric in milliseconds.
        
        Args:
            name: Name of the latency metric (e.g., "agent.run.latency.ms")
            tags: Optional dictionary of tag key/value pairs for adding
                dimensions to the metric (e.g., {"agent_id": "abc123"})
                
        Yields:
            None
            
        Example:
            ```python
            # Measure how long a function takes to execute
            with metrics.measure_latency("function.duration.ms", {"name": "process_data"}):
                process_data()
            ```
        """
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000.0
            self.record_histogram(name, latency_ms, tags)
    
    def export_metrics(self) -> None:
        """Export all collected metrics to registered exporters.
        
        This method manually triggers an export of all currently collected
        metrics to all registered exporters. It's useful for on-demand
        exports or when shutting down the application.
        
        If no exporters are registered, this method is a no-op.
        
        Note:
            This method catches and suppresses exceptions from individual
            exporters to ensure that a failure in one exporter doesn't
            prevent other exporters from receiving metrics.
        """
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
        """Start periodic export of metrics at specified intervals.
        
        Begins an asynchronous task that exports metrics at regular intervals.
        This is the recommended way to export metrics for ongoing monitoring.
        
        Args:
            interval_seconds: Time between exports in seconds (default: 15.0)
                
        Note:
            If periodic export is already running, this method is a no-op.
            The task runs until stop_periodic_export() is called or the
            application shuts down.
        """
        if self._is_exporting:
            return
            
        self._is_exporting = True
        self._export_task = asyncio.create_task(self._export_loop(interval_seconds))
    
    async def stop_periodic_export(self) -> None:
        """Stop periodic export of metrics.
        
        Cancels the background task that periodically exports metrics.
        Any metrics collected after this call will not be automatically
        exported until start_periodic_export() is called again.
        
        This method is asynchronous and waits for the export task to
        be fully cancelled before returning.
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
        """Shutdown the metrics collector and all exporters.
        
        Performs a clean shutdown of the metrics system:
        1. Cancels any running periodic export task
        2. Calls shutdown() on all registered exporters
        3. Clears the list of exporters
        
        This method should be called when the application is shutting down
        to ensure proper cleanup of resources.
        """
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
        """Record a metric of any type with name, value and optional tags.
        
        Internal method used by the public record_* methods to store a
        metric in the collector's memory.
        
        Args:
            name: Name of the metric
            value: Value of the metric
            metric_type: Type of the metric (COUNTER, GAUGE, HISTOGRAM, SUMMARY)
            tags: Optional dictionary of tag key/value pairs
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