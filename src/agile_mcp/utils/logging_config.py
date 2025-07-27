"""
Structured logging configuration for Agile MCP Server.

This module provides centralized logging configuration using structlog
for JSON-formatted output suitable for debugging and monitoring.
"""

import logging
import sys
from typing import Any, Dict, List, Optional

import structlog


def configure_logging(
    log_level: str = "INFO", enable_json: bool = True, enable_colors: bool = False
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: If True, output logs in JSON format
        enable_colors: If True, enable colored output (for development)
    """
    # Configure standard library logging with graceful fallback for invalid levels
    try:
        level = getattr(logging, log_level.upper())
    except AttributeError:
        # Fallback to INFO level for invalid log levels
        level = logging.INFO

    # Clear existing handlers to allow reconfiguration
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create and configure handler
    # Use a callable to get stderr so it respects mocking
    class StderrHandler(logging.StreamHandler):
        def __init__(self):
            super().__init__()

        @property
        def stream(self):
            return sys.stderr

        @stream.setter
        def stream(self, value):
            pass  # Ignore stream setter to always use current sys.stderr

    handler = StderrHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.setLevel(level)

    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # Configure structlog processors
    processors: List[Any] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if enable_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        if enable_colors:
            processors.append(structlog.dev.ConsoleRenderer())
        else:
            processors.append(structlog.processors.KeyValueRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,  # Disable cache to ensure proper
        # binding in tests
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured structlog logger instance
    """
    logger = structlog.get_logger(name)
    # Force logger to bind to ensure we return a BoundLogger instance
    if hasattr(logger, "bind"):
        return logger.bind()
    return logger


def create_request_context(
    request_id: Optional[str] = None, tool_name: Optional[str] = None, **kwargs: Any
) -> Dict[str, Any]:
    """
    Create request context for logging.

    Args:
        request_id: Unique request identifier
        tool_name: Name of the MCP tool being executed
        **kwargs: Additional context fields

    Returns:
        Dictionary of context fields for logging
    """
    context = {}

    if request_id:
        context["request_id"] = request_id
    if tool_name:
        context["tool_name"] = tool_name

    context.update(kwargs)
    return context


def create_entity_context(
    story_id: Optional[str] = None,
    epic_id: Optional[str] = None,
    artifact_id: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Create entity context for logging.

    Args:
        story_id: Story identifier
        epic_id: Epic identifier
        artifact_id: Artifact identifier
        **kwargs: Additional entity fields

    Returns:
        Dictionary of entity context fields for logging
    """
    context = {}

    if story_id:
        context["story_id"] = story_id
    if epic_id:
        context["epic_id"] = epic_id
    if artifact_id:
        context["artifact_id"] = artifact_id

    context.update(kwargs)
    return context
