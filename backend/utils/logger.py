"""
Logging configuration for NodeAI backend.

This module sets up structured logging with console and optional file output.
Logs are formatted consistently and can be configured via environment variables.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from backend.config import settings


def setup_logger(
    name: str = "nodai",
    log_file: Optional[Path] = None,
    log_level: Optional[str] = None,
) -> logging.Logger:
    """
    Set up and configure the application logger.

    Args:
        name: Logger name (default: "nodai")
        log_file: Optional path to log file. If None, uses settings.log_file
        log_level: Optional log level. If None, uses settings.log_level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level or settings.log_level))

    # Prevent duplicate handlers if logger is already configured
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if log_file is specified)
    log_file_path = log_file or (Path(settings.log_file) if settings.log_file else None)
    if log_file_path:
        # Ensure log directory exists
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(getattr(logging, settings.log_level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Module name (e.g., __name__). If None, uses "nodai"

    Returns:
        Logger instance configured with application settings

    Example:
        ```python
        from backend.utils.logger import get_logger

        logger = get_logger(__name__)
        logger.info("Application started")
        ```
    """
    if name is None:
        name = "nodai"

    # Use the main logger if name starts with "nodai" or is "nodai"
    if name == "nodai" or name.startswith("nodai."):
        logger_name = name
    else:
        # For module loggers, use nodai.module_name format
        logger_name = f"nodai.{name}"

    logger = logging.getLogger(logger_name)

    # If logger doesn't have handlers, set it up
    if not logger.handlers:
        setup_logger(logger_name)

    return logger


# Create the main application logger
# This will be imported and used as the default logger
main_logger = setup_logger("nodai")

