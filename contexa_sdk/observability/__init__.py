"""Observability module for Contexa SDK."""

from contexa_sdk.observability.logger import get_logger, set_log_level
from contexa_sdk.observability.tracer import trace, get_tracer, Span, SpanKind, SpanStatus
from contexa_sdk.observability.metrics import record_metric

# Import visualization functions conditionally to avoid hard dependency
try:
    from contexa_sdk.observability.visualization import (
        draw_graph, get_agent_team_graph, export_graph_to_json
    )
    __viz_available__ = True
except ImportError:
    __viz_available__ = False
    # Create placeholder functions that raise ImportError when called
    def _viz_not_available(*args, **kwargs):
        raise ImportError(
            "Visualization dependencies not installed. "
            "Install with `pip install contexa-sdk[viz]`."
        )
    
    draw_graph = get_agent_team_graph = export_graph_to_json = _viz_not_available

__all__ = [
    "get_logger",
    "set_log_level",
    "trace",
    "get_tracer",
    "Span",
    "SpanKind",
    "SpanStatus",
    "record_metric",
    "draw_graph",
    "get_agent_team_graph",
    "export_graph_to_json",
] 