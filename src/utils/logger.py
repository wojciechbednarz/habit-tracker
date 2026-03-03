"""Utility module for setting up a consistent logger across all modules."""

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


def setup_logger(name: str = "", level: int | str = logging.INFO) -> structlog.stdlib.BoundLogger:
    """
    Set up a consistent logger across all modules
    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    Returns:
        Configured logger instance
    """
    stdlib_logger = logging.getLogger(name or __name__)
    if not stdlib_logger.handlers:
        stdlib_logger.propagate = False
        stdlib_logger.setLevel(level if isinstance(level, int) else getattr(logging, level.upper()))
        json_formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
        )

        console_formatter = structlog.stdlib.ProcessorFormatter(processor=structlog.dev.ConsoleRenderer(colors=True))

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        stdlib_logger.addHandler(console_handler)

        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_path = log_dir / f"app_{datetime.now(tz=UTC).strftime('%Y%m%d')}.log"

        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(json_formatter)

        stdlib_logger.addHandler(file_handler)

    return structlog.wrap_logger(stdlib_logger)
