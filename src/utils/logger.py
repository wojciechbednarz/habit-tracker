"""Utility module for setting up a consistent logger across all modules."""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(name: str = "", level: int | str = logging.INFO) -> logging.Logger:
    """
    Set up a consistent logger across all modules
    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name or __name__)

    if logger.handlers:
        return logger
    if isinstance(level, str):
        logger.setLevel(getattr(logging, level.upper()))
    else:
        logger.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    file_handler = logging.FileHandler(
        log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
