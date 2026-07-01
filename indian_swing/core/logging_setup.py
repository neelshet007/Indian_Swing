"""
Structured logging setup using structlog + rich.
Call configure_logging() once at application startup.
All modules obtain a logger via: logger = get_logger(__name__)
"""
from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from rich.console import Console
from rich.logging import RichHandler


_console = Console(stderr=True)


def configure_logging(level: str = "INFO", fmt: str = "json") -> None:
    """
    Initialize structlog with either JSON (production) or console (development) rendering.

    Args:
        level: Python logging level string e.g. "INFO", "DEBUG".
        fmt: "json" for structured JSON lines, "console" for human-readable rich output.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if fmt == "json":
        renderer = structlog.processors.JSONRenderer()
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter())
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)
        handler = RichHandler(
            console=_console,
            rich_tracebacks=True,
            show_path=False,
        )

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Quiet noisy third-party loggers
    for noisy in ("yfinance", "peewee", "urllib3", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger for the given module name."""
    return structlog.get_logger(name)
