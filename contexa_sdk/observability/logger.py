"""Logging utilities for Contexa SDK.

This module provides standardized logging utilities for the Contexa SDK,
including structured logging, JSON formatting, and consistent configuration
across different components. It supports both traditional text-based logging
and structured JSON logging for integration with log aggregation systems.
"""

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
    """Get a configured logger with the given name.
    
    Creates or retrieves a logger with the specified name that inherits
    settings from the root logger. This ensures consistent formatting and
    behavior across all loggers in the application.
    
    Args:
        name: Name of the logger, typically using dot notation to indicate
            hierarchy (e.g., 'contexa.core.agent')
        
    Returns:
        A configured logger instance ready for use
        
    Example:
        ```python
        logger = get_logger('contexa.agents.search')
        logger.info("Processing search request")
        logger.error("Search failed", extra={"query": "example", "error_code": 404})
        ```
    """
    return logging.getLogger(name)


def set_log_level(level: Union[str, int]) -> None:
    """Set the global log level for all Contexa loggers.
    
    Updates the log level for the root logger and all its handlers,
    which affects all loggers in the application. This provides a
    convenient way to adjust verbosity at runtime.
    
    Args:
        level: Log level as either a string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            or a corresponding integer constant from the logging module
            
    Raises:
        ValueError: If the string level name is not valid
        
    Example:
        ```python
        # Set to debug level using string
        set_log_level('DEBUG')
        
        # Set to info level using constant
        set_log_level(logging.INFO)
        
        # Reduce verbosity for production
        set_log_level('WARNING')
        ```
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
    """Configure global logging settings for the Contexa SDK.
    
    Sets up the root logger with appropriate handlers and formatters
    based on the specified configuration. This should typically be
    called once at application startup.
    
    Args:
        level: Log level as either a string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            or a corresponding integer constant from the logging module
        output_format: Output format specifier, either 'text' for human-readable
            logs or 'json' for structured logs suitable for machine processing
        log_file: Optional path to a file where logs should be written in addition
            to standard output. If None, logs are only written to stdout.
        structured: Whether to use structured logging with additional context
            fields. When True, forces JSON formatting regardless of output_format.
            
    Example:
        ```python
        # Basic text logging to console
        configure_logging(level='INFO')
        
        # JSON-formatted logs written to both console and file
        configure_logging(
            level=logging.DEBUG,
            output_format='json',
            log_file='/var/log/contexa.log'
        )
        
        # Structured logging with additional context
        configure_logging(level='INFO', structured=True)
        logger = get_logger('app')
        logger.info("User login", extra={"user_id": "123", "source_ip": "192.168.1.1"})
        ```
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
    """Formatter that outputs log records as structured JSON.
    
    This formatter converts standard Python logging records into JSON objects
    with a consistent structure, making them suitable for ingestion by log
    aggregation and analysis tools. It preserves all standard logging fields
    and includes any extra contextual information provided in the log call.
    
    The JSON format includes:
    - timestamp: ISO 8601 formatted timestamp
    - level: Log level name (INFO, ERROR, etc.)
    - name: Logger name
    - message: Log message
    - exception: Exception information (if present)
    - Any additional fields provided via the extra parameter
    
    Example output:
    ```json
    {
        "timestamp": "2023-06-15T14:32:10.123456Z",
        "level": "ERROR",
        "name": "contexa.agent",
        "message": "Failed to process request",
        "exception": "Traceback (most recent call last)...",
        "user_id": "user123",
        "request_id": "req-456"
    }
    ```
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string.
        
        Converts a standard logging.LogRecord object into a JSON string
        containing all relevant fields and any additional context provided
        in the original log call.
        
        Args:
            record: The log record to format
            
        Returns:
            A JSON string representing the log record with all its fields
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
    """Log a structured event with standardized formatting.
    
    This function is designed for logging business or system events with
    consistent structure and additional context. Events are distinct from
    regular logs in that they represent meaningful occurrences in the system
    rather than just diagnostic information.
    
    All events are logged to the 'contexa.events' logger and include an
    'event' field with the event name, plus any additional data provided.
    
    Args:
        event: Name of the event (e.g., 'user_login', 'agent_handoff')
        level: Log level for the event, either as a string ('INFO', 'ERROR')
            or a corresponding integer constant from the logging module
        data: Optional dictionary of additional data to include with the event,
            such as user IDs, request details, or other context
            
    Example:
        ```python
        # Log a simple event
        log_event('agent_created', level='INFO')
        
        # Log an event with additional context
        log_event(
            'request_processed', 
            level=logging.INFO, 
            data={
                'user_id': '123',
                'request_id': 'req-456',
                'duration_ms': 237,
                'status': 'success'
            }
        )
        ```
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