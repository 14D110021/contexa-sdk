"""Logging module for Contexa SDK."""

import os
import sys
import json
import logging
import threading
from typing import Any, Dict, Optional, Union

# Configure the default logger
_default_log_level = os.environ.get("CONTEXA_LOG_LEVEL", "INFO").upper()
_loggers = {}
_logger_lock = threading.RLock()


class ContextaLogger(logging.Logger):
    """Logger for Contexa SDK with structured logging support."""
    
    def __init__(self, name: str, level: int = logging.NOTSET):
        """Initialize the logger.
        
        Args:
            name: Name of the logger
            level: Log level
        """
        super().__init__(name, level)
    
    def _log_with_context(self, level: int, msg: str, context: Dict[str, Any], *args, **kwargs):
        """Log with context information.
        
        Args:
            level: Log level
            msg: Log message
            context: Context information to include in the log
            *args: Additional arguments
            **kwargs: Additional keyword arguments
        """
        if self.isEnabledFor(level):
            # Add context to extra
            kwargs.setdefault("extra", {}).update({"context": context})
            self._log(level, msg, args, **kwargs)
    
    def debug_with_context(self, msg: str, context: Dict[str, Any], *args, **kwargs):
        """Log debug message with context.
        
        Args:
            msg: Log message
            context: Context information to include in the log
            *args: Additional arguments
            **kwargs: Additional keyword arguments
        """
        self._log_with_context(logging.DEBUG, msg, context, *args, **kwargs)
    
    def info_with_context(self, msg: str, context: Dict[str, Any], *args, **kwargs):
        """Log info message with context.
        
        Args:
            msg: Log message
            context: Context information to include in the log
            *args: Additional arguments
            **kwargs: Additional keyword arguments
        """
        self._log_with_context(logging.INFO, msg, context, *args, **kwargs)
    
    def warning_with_context(self, msg: str, context: Dict[str, Any], *args, **kwargs):
        """Log warning message with context.
        
        Args:
            msg: Log message
            context: Context information to include in the log
            *args: Additional arguments
            **kwargs: Additional keyword arguments
        """
        self._log_with_context(logging.WARNING, msg, context, *args, **kwargs)
    
    def error_with_context(self, msg: str, context: Dict[str, Any], *args, **kwargs):
        """Log error message with context.
        
        Args:
            msg: Log message
            context: Context information to include in the log
            *args: Additional arguments
            **kwargs: Additional keyword arguments
        """
        self._log_with_context(logging.ERROR, msg, context, *args, **kwargs)
    
    def critical_with_context(self, msg: str, context: Dict[str, Any], *args, **kwargs):
        """Log critical message with context.
        
        Args:
            msg: Log message
            context: Context information to include in the log
            *args: Additional arguments
            **kwargs: Additional keyword arguments
        """
        self._log_with_context(logging.CRITICAL, msg, context, *args, **kwargs)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string
        """
        # Extract standard fields
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        # Add location data
        log_data.update({
            "filename": record.filename,
            "lineno": record.lineno,
            "funcName": record.funcName,
        })
        
        # Add trace and span IDs if available
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        if hasattr(record, "span_id"):
            log_data["span_id"] = record.span_id
        
        # Add context if available
        if hasattr(record, "context") and record.context:
            log_data["context"] = record.context
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def _create_console_handler() -> logging.Handler:
    """Create a console handler for logging.
    
    Returns:
        A configured console handler
    """
    # Create console handler and set level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter based on environment
    if os.environ.get("CONTEXA_LOG_FORMAT", "").upper() == "JSON":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    return console_handler


def get_logger(name: str) -> ContextaLogger:
    """Get a logger with the given name.
    
    Args:
        name: Name for the logger
        
    Returns:
        A configured logger
    """
    with _logger_lock:
        if name in _loggers:
            return _loggers[name]
        
        # Create logger
        logging.setLoggerClass(ContextaLogger)
        logger = logging.getLogger(name)
        
        # Set level
        try:
            level = getattr(logging, _default_log_level)
        except AttributeError:
            level = logging.INFO
        logger.setLevel(level)
        
        # Add a console handler for output
        logger.addHandler(_create_console_handler())
        
        # Store and return the logger
        _loggers[name] = logger
        return logger


def set_log_level(level: Union[str, int]) -> None:
    """Set the log level for all loggers.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    global _default_log_level
    
    # Convert string level to int if needed
    if isinstance(level, str):
        level = level.upper()
        numeric_level = getattr(logging, level, None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {level}")
        level = numeric_level
    
    # Update default level
    _default_log_level = level
    
    # Update all existing loggers
    with _logger_lock:
        for logger in _loggers.values():
            logger.setLevel(level)
            
            # Update handlers as well
            for handler in logger.handlers:
                handler.setLevel(level) 