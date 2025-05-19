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