"""Logging utilities for Contexa SDK."""

import logging
import sys
import os
import json
from typing import Dict, Any, Optional, Union


# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.
    
    Args:
        name: Name of the logger
        
    Returns:
        Configured logger
    """
    return logging.getLogger(name)


def set_log_level(level: Union[str, int]) -> None:
    """Set the log level for all loggers.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = level.upper()
        numeric_level = getattr(logging, level, None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {level}")
        level = numeric_level
    
    # Update root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Update handlers as well
    for handler in root_logger.handlers:
        handler.setLevel(level)


def configure_logging(
    level: Union[int, str] = logging.INFO,
    output_format: str = "text",
    log_file: Optional[str] = None,
    structured: bool = False
) -> None:
    """Configure global logging settings.
    
    Args:
        level: Log level
        output_format: Output format ('text' or 'json')
        log_file: Optional file to write logs to
        structured: Whether to use structured logging
    """
    # Convert string level to constant if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Configure formatter
    if output_format.lower() == "json" or structured:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


class JsonFormatter(logging.Formatter):
    """Formatter that outputs log records as JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string representation of the log record
        """
        log_data = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra attributes
        for key, value in record.__dict__.items():
            if key not in {
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread", "threadName"
            }:
                log_data[key] = value
        
        return json.dumps(log_data)


def log_event(
    event: str,
    level: Union[int, str] = logging.INFO,
    data: Optional[Dict[str, Any]] = None
) -> None:
    """Log a structured event.
    
    Args:
        event: Event name
        level: Log level
        data: Additional event data
    """
    # Convert string level to constant if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    logger = get_logger("contexa.events")
    
    # Create structured log record
    extra = {"event": event}
    if data:
        extra.update(data)
    
    # Log the event
    logger.log(level, event, extra=extra) 