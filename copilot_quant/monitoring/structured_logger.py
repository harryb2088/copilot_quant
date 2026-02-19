"""
Structured JSON Logging

Provides structured logging with JSON output for better log analysis
and integration with log aggregation tools.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Format log records as JSON"""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class StructuredLogger:
    """
    Structured logger with JSON output.

    Provides enhanced logging with structured fields for better
    log analysis and monitoring.

    Example:
        >>> logger = StructuredLogger('myapp')
        >>> logger.info('User logged in', user_id=123, session='abc')
        >>> logger.error('Database error', error_code=500, retry_count=3)
    """

    def __init__(self, name: str, level: int = logging.INFO, log_file: Optional[Path] = None, json_format: bool = True):
        """
        Initialize structured logger.

        Args:
            name: Logger name
            level: Logging level (default: INFO)
            log_file: Optional file path for file logging
            json_format: Use JSON formatting (default: True)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False

        # Clear existing handlers
        self.logger.handlers = []

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        if json_format:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

        self.logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)

            if json_format:
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

            self.logger.addHandler(file_handler)

    def _log_with_fields(self, level: int, msg: str, **fields: Any):
        """Log message with structured fields"""
        extra = {"extra_fields": fields} if fields else {}
        self.logger.log(level, msg, extra=extra)

    def debug(self, msg: str, **fields: Any):
        """Log debug message with optional fields"""
        self._log_with_fields(logging.DEBUG, msg, **fields)

    def info(self, msg: str, **fields: Any):
        """Log info message with optional fields"""
        self._log_with_fields(logging.INFO, msg, **fields)

    def warning(self, msg: str, **fields: Any):
        """Log warning message with optional fields"""
        self._log_with_fields(logging.WARNING, msg, **fields)

    def error(self, msg: str, **fields: Any):
        """Log error message with optional fields"""
        self._log_with_fields(logging.ERROR, msg, **fields)

    def critical(self, msg: str, **fields: Any):
        """Log critical message with optional fields"""
        self._log_with_fields(logging.CRITICAL, msg, **fields)

    def exception(self, msg: str, **fields: Any):
        """Log exception with traceback and optional fields"""
        extra = {"extra_fields": fields} if fields else {}
        self.logger.exception(msg, extra=extra)


# Global logger cache
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(
    name: str, level: int = logging.INFO, log_file: Optional[Path] = None, json_format: bool = True
) -> StructuredLogger:
    """
    Get or create a structured logger.

    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        json_format: Use JSON formatting

    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, level, log_file, json_format)

    return _loggers[name]


def configure_logging(level: int = logging.INFO, log_dir: Optional[Path] = None, json_format: bool = True):
    """
    Configure application-wide logging.

    Args:
        level: Default logging level
        log_dir: Directory for log files
        json_format: Use JSON formatting
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    root_logger.addHandler(console_handler)

    # File handler if log directory specified
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"copilot_quant_{datetime.now().strftime('%Y%m%d')}.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)

        if json_format:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

        root_logger.addHandler(file_handler)
