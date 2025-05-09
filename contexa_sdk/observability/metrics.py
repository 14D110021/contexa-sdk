"""Metrics collection module for Contexa SDK."""

import os
import time
import json
import threading
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# Import logger
from contexa_sdk.observability.logger import get_logger

# Create a logger for this module
logger = get_logger(__name__)

# Global metrics registry and lock
_metrics_registry = {}
_metrics_lock = threading.RLock()
_flush_thread = None
_flush_interval = int(os.environ.get("CONTEXA_METRICS_FLUSH_INTERVAL", "60"))  # Seconds
_should_flush = False


class MetricType(str, Enum):
    """Type of metric."""
    
    COUNTER = "counter"  # Cumulative value that only increases
    GAUGE = "gauge"  # Value that can go up and down
    HISTOGRAM = "histogram"  # Distribution of values


class CounterMetric:
    """Counter metric that only increases."""
    
    def __init__(self, name: str, description: str, labels: List[str] = None):
        """Initialize a counter metric.
        
        Args:
            name: Name of the metric
            description: Description of the metric
            labels: List of label names that can be used with this metric
        """
        self.name = name
        self.description = description
        self.labels = labels or []
        self.values: Dict[str, float] = {}
    
    def inc(self, value: float = 1.0, **labels) -> None:
        """Increment the counter.
        
        Args:
            value: Value to increment by
            **labels: Label values
        """
        if value < 0:
            logger.warning(f"Counter {self.name} cannot be decremented, ignoring value {value}")
            return
            
        label_key = self._label_key(**labels)
        
        with _metrics_lock:
            if label_key in self.values:
                self.values[label_key] += value
            else:
                self.values[label_key] = value
    
    def get(self, **labels) -> float:
        """Get the current value of the counter.
        
        Args:
            **labels: Label values
            
        Returns:
            Current value of the counter
        """
        label_key = self._label_key(**labels)
        
        with _metrics_lock:
            return self.values.get(label_key, 0.0)
    
    def _label_key(self, **labels) -> str:
        """Generate a key for the given labels.
        
        Args:
            **labels: Label values
            
        Returns:
            Key for the labels
        """
        # Validate labels
        for label in labels:
            if label not in self.labels:
                logger.warning(f"Unexpected label {label} for metric {self.name}")
        
        # Build a sorted key from labels
        label_parts = []
        for label in sorted(self.labels):
            label_parts.append(f"{label}={labels.get(label, '')}")
        return "#".join(label_parts) or "_default_"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary.
        
        Returns:
            Dictionary representation of the metric
        """
        # Parse label keys into dictionaries
        result = []
        for label_key, value in self.values.items():
            if label_key == "_default_":
                result.append({
                    "value": value,
                    "labels": {},
                })
            else:
                labels = {}
                for label_part in label_key.split("#"):
                    if "=" in label_part:
                        label_name, label_value = label_part.split("=", 1)
                        labels[label_name] = label_value
                result.append({
                    "value": value,
                    "labels": labels,
                })
        
        return {
            "name": self.name,
            "description": self.description,
            "type": MetricType.COUNTER.value,
            "values": result,
        }


class GaugeMetric:
    """Gauge metric that can go up or down."""
    
    def __init__(self, name: str, description: str, labels: List[str] = None):
        """Initialize a gauge metric.
        
        Args:
            name: Name of the metric
            description: Description of the metric
            labels: List of label names that can be used with this metric
        """
        self.name = name
        self.description = description
        self.labels = labels or []
        self.values: Dict[str, float] = {}
    
    def set(self, value: float, **labels) -> None:
        """Set the gauge to a specific value.
        
        Args:
            value: Value to set
            **labels: Label values
        """
        label_key = self._label_key(**labels)
        
        with _metrics_lock:
            self.values[label_key] = value
    
    def inc(self, value: float = 1.0, **labels) -> None:
        """Increment the gauge.
        
        Args:
            value: Value to increment by
            **labels: Label values
        """
        label_key = self._label_key(**labels)
        
        with _metrics_lock:
            if label_key in self.values:
                self.values[label_key] += value
            else:
                self.values[label_key] = value
    
    def dec(self, value: float = 1.0, **labels) -> None:
        """Decrement the gauge.
        
        Args:
            value: Value to decrement by
            **labels: Label values
        """
        self.inc(-value, **labels)
    
    def get(self, **labels) -> float:
        """Get the current value of the gauge.
        
        Args:
            **labels: Label values
            
        Returns:
            Current value of the gauge
        """
        label_key = self._label_key(**labels)
        
        with _metrics_lock:
            return self.values.get(label_key, 0.0)
    
    def _label_key(self, **labels) -> str:
        """Generate a key for the given labels.
        
        Args:
            **labels: Label values
            
        Returns:
            Key for the labels
        """
        # Validate labels
        for label in labels:
            if label not in self.labels:
                logger.warning(f"Unexpected label {label} for metric {self.name}")
        
        # Build a sorted key from labels
        label_parts = []
        for label in sorted(self.labels):
            label_parts.append(f"{label}={labels.get(label, '')}")
        return "#".join(label_parts) or "_default_"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary.
        
        Returns:
            Dictionary representation of the metric
        """
        # Parse label keys into dictionaries
        result = []
        for label_key, value in self.values.items():
            if label_key == "_default_":
                result.append({
                    "value": value,
                    "labels": {},
                })
            else:
                labels = {}
                for label_part in label_key.split("#"):
                    if "=" in label_part:
                        label_name, label_value = label_part.split("=", 1)
                        labels[label_name] = label_value
                result.append({
                    "value": value,
                    "labels": labels,
                })
        
        return {
            "name": self.name,
            "description": self.description,
            "type": MetricType.GAUGE.value,
            "values": result,
        }


class HistogramMetric:
    """Histogram metric to track distributions of values."""
    
    def __init__(
        self,
        name: str,
        description: str,
        buckets: List[float] = None,
        labels: List[str] = None,
    ):
        """Initialize a histogram metric.
        
        Args:
            name: Name of the metric
            description: Description of the metric
            buckets: Bucket boundaries for the histogram
            labels: List of label names that can be used with this metric
        """
        self.name = name
        self.description = description
        self.buckets = sorted(buckets or [0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0])
        self.labels = labels or []
        self.values: Dict[str, Dict[str, float]] = {}
    
    def observe(self, value: float, **labels) -> None:
        """Observe a value.
        
        Args:
            value: Value to observe
            **labels: Label values
        """
        label_key = self._label_key(**labels)
        
        with _metrics_lock:
            if label_key not in self.values:
                self.values[label_key] = {
                    "sum": 0.0,
                    "count": 0,
                    "buckets": {str(b): 0 for b in self.buckets},
                }
            
            self.values[label_key]["sum"] += value
            self.values[label_key]["count"] += 1
            
            # Increment bucket counters
            for bucket in self.buckets:
                if value <= bucket:
                    self.values[label_key]["buckets"][str(bucket)] += 1
    
    def get(self, **labels) -> Dict[str, Any]:
        """Get the current value of the histogram.
        
        Args:
            **labels: Label values
            
        Returns:
            Current value of the histogram
        """
        label_key = self._label_key(**labels)
        
        with _metrics_lock:
            return self.values.get(label_key, {
                "sum": 0.0,
                "count": 0,
                "buckets": {str(b): 0 for b in self.buckets},
            })
    
    def _label_key(self, **labels) -> str:
        """Generate a key for the given labels.
        
        Args:
            **labels: Label values
            
        Returns:
            Key for the labels
        """
        # Validate labels
        for label in labels:
            if label not in self.labels:
                logger.warning(f"Unexpected label {label} for metric {self.name}")
        
        # Build a sorted key from labels
        label_parts = []
        for label in sorted(self.labels):
            label_parts.append(f"{label}={labels.get(label, '')}")
        return "#".join(label_parts) or "_default_"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary.
        
        Returns:
            Dictionary representation of the metric
        """
        # Parse label keys into dictionaries
        result = []
        for label_key, value in self.values.items():
            if label_key == "_default_":
                result.append({
                    "value": value,
                    "labels": {},
                })
            else:
                labels = {}
                for label_part in label_key.split("#"):
                    if "=" in label_part:
                        label_name, label_value = label_part.split("=", 1)
                        labels[label_name] = label_value
                result.append({
                    "value": value,
                    "labels": labels,
                })
        
        return {
            "name": self.name,
            "description": self.description,
            "type": MetricType.HISTOGRAM.value,
            "buckets": self.buckets,
            "values": result,
        }


def counter(name: str, description: str, labels: List[str] = None) -> CounterMetric:
    """Create or get a counter metric.
    
    Args:
        name: Name of the metric
        description: Description of the metric
        labels: List of label names that can be used with this metric
        
    Returns:
        Counter metric
    """
    with _metrics_lock:
        metric_key = f"counter:{name}"
        
        if metric_key in _metrics_registry:
            return _metrics_registry[metric_key]
        
        metric = CounterMetric(name, description, labels)
        _metrics_registry[metric_key] = metric
        
        return metric


def gauge(name: str, description: str, labels: List[str] = None) -> GaugeMetric:
    """Create or get a gauge metric.
    
    Args:
        name: Name of the metric
        description: Description of the metric
        labels: List of label names that can be used with this metric
        
    Returns:
        Gauge metric
    """
    with _metrics_lock:
        metric_key = f"gauge:{name}"
        
        if metric_key in _metrics_registry:
            return _metrics_registry[metric_key]
        
        metric = GaugeMetric(name, description, labels)
        _metrics_registry[metric_key] = metric
        
        return metric


def histogram(
    name: str,
    description: str,
    buckets: List[float] = None,
    labels: List[str] = None,
) -> HistogramMetric:
    """Create or get a histogram metric.
    
    Args:
        name: Name of the metric
        description: Description of the metric
        buckets: Bucket boundaries for the histogram
        labels: List of label names that can be used with this metric
        
    Returns:
        Histogram metric
    """
    with _metrics_lock:
        metric_key = f"histogram:{name}"
        
        if metric_key in _metrics_registry:
            return _metrics_registry[metric_key]
        
        metric = HistogramMetric(name, description, buckets, labels)
        _metrics_registry[metric_key] = metric
        
        return metric


class Timer:
    """Timer for measuring the duration of an operation."""
    
    def __init__(self, metric: HistogramMetric = None, **labels):
        """Initialize a timer.
        
        Args:
            metric: Histogram metric to update with the duration
            **labels: Labels for the metric
        """
        self.metric = metric
        self.labels = labels
        self.start_time = None
        self.end_time = None
    
    def __enter__(self) -> "Timer":
        """Enter the timer context.
        
        Returns:
            Self, for use in context managers
        """
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the timer context.
        
        Args:
            exc_type: Exception type, if any
            exc_val: Exception value, if any
            exc_tb: Exception traceback, if any
        """
        self.stop()
    
    def start(self) -> None:
        """Start the timer."""
        self.start_time = time.time()
    
    def stop(self) -> float:
        """Stop the timer and return the duration.
        
        Returns:
            Duration in seconds
        """
        self.end_time = time.time()
        duration = self.duration()
        
        if self.metric:
            self.metric.observe(duration, **self.labels)
        
        return duration
    
    def duration(self) -> float:
        """Get the current duration.
        
        Returns:
            Duration in seconds
        """
        end_time = self.end_time or time.time()
        
        if self.start_time is None:
            return 0.0
        
        return end_time - self.start_time


def record_metric(
    metric_type: str,
    name: str,
    value: float,
    description: str = "",
    labels: Dict[str, str] = None,
) -> None:
    """Record a metric value.
    
    This is a convenience function for recording metrics without creating
    metric objects directly.
    
    Args:
        metric_type: Type of metric (counter, gauge, histogram)
        name: Name of the metric
        value: Value to record
        description: Description of the metric
        labels: Labels for the metric
    """
    metric_type = metric_type.lower()
    labels = labels or {}
    
    if metric_type == "counter":
        counter(name, description, list(labels.keys())).inc(value, **labels)
    elif metric_type == "gauge":
        gauge(name, description, list(labels.keys())).set(value, **labels)
    elif metric_type == "histogram":
        histogram(name, description, labels=list(labels.keys())).observe(value, **labels)
    else:
        logger.warning(f"Unknown metric type: {metric_type}")


def _flush_metrics() -> None:
    """Flush metrics to storage."""
    global _should_flush
    
    with _metrics_lock:
        metrics = []
        for metric in _metrics_registry.values():
            metrics.append(metric.to_dict())
    
    # Determine storage based on environment
    exporter = os.environ.get("CONTEXA_METRICS_EXPORTER", "console").lower()
    
    if exporter == "console":
        # Just log the metrics
        logger.info(f"Metrics snapshot: {len(metrics)} metrics")
        for metric in metrics:
            logger.info(f"Metric: {metric['name']}", extra={"metric": metric})
    elif exporter == "file":
        # Save to a file
        try:
            metrics_dir = os.environ.get("CONTEXA_METRICS_DIR", "./.ctx/metrics")
            os.makedirs(metrics_dir, exist_ok=True)
            
            filename = f"{metrics_dir}/metrics_{int(time.time())}.json"
            with open(filename, "w") as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics to file: {str(e)}")
    elif exporter == "prometheus":
        # Would export to Prometheus
        logger.info("Would export metrics to Prometheus")
    else:
        # Unknown exporter
        logger.warning(f"Unknown metrics exporter: {exporter}")
    
    # Check if we should keep flushing
    if _should_flush:
        _schedule_flush()


def _schedule_flush() -> None:
    """Schedule a metrics flush."""
    global _flush_thread
    
    if _flush_thread is not None and _flush_thread.is_alive():
        return
    
    _flush_thread = threading.Timer(_flush_interval, _flush_metrics)
    _flush_thread.daemon = True
    _flush_thread.start()


def start_metrics_collection() -> None:
    """Start collecting metrics."""
    global _should_flush
    
    _should_flush = True
    _schedule_flush()


def stop_metrics_collection() -> None:
    """Stop collecting metrics."""
    global _should_flush, _flush_thread
    
    _should_flush = False
    
    if _flush_thread is not None:
        _flush_thread.cancel()
        _flush_thread = None
    
    # Final flush
    _flush_metrics()


# Initialize standard metrics
agent_requests = counter(
    "agent_requests_total",
    "Total number of requests to agents",
    ["agent_id", "agent_name", "status"],
)

agent_latency = histogram(
    "agent_latency_seconds",
    "Latency of agent requests",
    [0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0],
    ["agent_id", "agent_name"],
)

model_tokens = counter(
    "model_tokens_total",
    "Total number of tokens used by models",
    ["model_name", "provider", "type"],
)

tool_calls = counter(
    "tool_calls_total",
    "Total number of tool calls",
    ["tool_name", "agent_id", "status"],
)

tool_latency = histogram(
    "tool_latency_seconds",
    "Latency of tool calls",
    [0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0],
    ["tool_name", "agent_id"],
)

handoffs = counter(
    "handoffs_total",
    "Total number of agent handoffs",
    ["source_agent_id", "target_agent_id", "status"],
)

active_agents = gauge(
    "active_agents",
    "Number of currently active agents",
)

# Start metrics collection if auto-start is enabled
if os.environ.get("CONTEXA_METRICS_AUTO_START", "true").lower() == "true":
    start_metrics_collection() 