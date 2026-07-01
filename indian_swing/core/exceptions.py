"""
Domain exception hierarchy.
All platform exceptions flow from SwingBaseError so callers can catch at any granularity.
"""
from __future__ import annotations


class SwingBaseError(Exception):
    """Root exception for the entire platform."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


# ── Data exceptions ──────────────────────────────────────────────────────────

class DataError(SwingBaseError):
    """Base for data layer errors."""


class DataProviderError(DataError):
    """External data provider failed to return data."""


class DataValidationError(DataError):
    """Downloaded or stored data failed validation."""


class DataNotFoundError(DataError):
    """Requested data does not exist."""


class InsufficientDataError(DataError):
    """Not enough data points to compute indicators or run strategy."""


# ── Database exceptions ───────────────────────────────────────────────────────

class DatabaseError(SwingBaseError):
    """Base for database layer errors."""


class RecordNotFoundError(DatabaseError):
    """Queried record does not exist."""


class DuplicateRecordError(DatabaseError):
    """Insert would violate uniqueness constraint."""


# ── Strategy / Indicator exceptions ──────────────────────────────────────────

class StrategyError(SwingBaseError):
    """Base for strategy errors."""


class StrategyNotFoundError(StrategyError):
    """Requested strategy is not registered."""


class StrategyConfigError(StrategyError):
    """Strategy received invalid configuration."""


class IndicatorError(SwingBaseError):
    """Indicator computation failed."""


# ── Engine exceptions ─────────────────────────────────────────────────────────

class EngineError(SwingBaseError):
    """Core engine encountered an unrecoverable error."""


class ScanError(EngineError):
    """Market scan failed for a stock or globally."""


# ── Backtesting exceptions ────────────────────────────────────────────────────

class BacktestError(SwingBaseError):
    """Backtesting engine error."""


# ── Replay exceptions ─────────────────────────────────────────────────────────

class ReplayError(SwingBaseError):
    """Replay engine error."""


class ReplaySessionNotFoundError(ReplayError):
    """Requested replay session does not exist."""


# ── Configuration exceptions ──────────────────────────────────────────────────

class ConfigurationError(SwingBaseError):
    """Platform misconfiguration detected."""
