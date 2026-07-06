"""
BaseStrategy contract.
Strategies inherit this, implement generate_signals(), and are auto-discovered.
The engine never imports strategy classes directly.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import pandas as pd

from indian_swing.core.types import (
    RiskLevel,
    Score,
    SignalDirection,
    SignalQuality,
    Symbol,
)


@dataclass
class StrategySignal:
    """Standardized output from every strategy — the engine only knows this type."""

    symbol: Symbol
    direction: SignalDirection
    entry_price: float
    stop_loss: float
    target_1: float
    target_2: float | None
    confidence_score: Score              # 0.0 – 1.0
    quality: SignalQuality
    risk_level: RiskLevel
    holding_days: int
    reasons: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.entry_price = float(self.entry_price)
        self.stop_loss = float(self.stop_loss)
        if self.target_1 is not None:
            self.target_1 = float(self.target_1)
        if self.target_2 is not None:
            self.target_2 = float(self.target_2)
        if self.confidence_score is not None:
            self.confidence_score = float(self.confidence_score)
        if self.holding_days is not None:
            self.holding_days = int(self.holding_days)
        if self.metadata:
            cleaned = {}
            for k, v in self.metadata.items():
                if hasattr(v, "item"):
                    cleaned[k] = v.item()
                else:
                    cleaned[k] = v
            self.metadata = cleaned

    @property
    def risk_reward(self) -> float:
        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.target_1 - self.entry_price)
        return round(reward / risk, 2) if risk > 0 else 0.0

    @property
    def risk_pct(self) -> float:
        return round(abs(self.entry_price - self.stop_loss) / self.entry_price * 100, 2)


class BaseStrategy(ABC):
    """
    All strategies must inherit from this.
    Implement generate_signals() and optionally required_lookback.

    Engine contract:
    - The engine provides a clean OHLCV DataFrame up to the analysis date.
    - Strategies must not access external data or databases.
    - Strategies must not have side effects.
    - Strategies must be stateless between calls.
    """

    #: Minimum bars required before strategy can produce reliable signals.
    required_lookback: int = 200

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique strategy identifier e.g. 'EMABreakout'."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable strategy description."""
        ...

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def default_params(self) -> dict[str, Any]:
        """Override to provide configurable defaults."""
        return {}

    @abstractmethod
    def generate_signals(
        self,
        symbol: Symbol,
        df: pd.DataFrame,
        as_of_date: date | None = None,
    ) -> list[StrategySignal]:
        """
        Analyze the DataFrame and return zero or more signals.

        Args:
            symbol: Stock symbol.
            df: OHLCV DataFrame up to as_of_date (no lookahead).
            as_of_date: Analysis date (last bar date if None).

        Returns:
            List of StrategySignal objects. Empty list = no signal.
        """
        ...

    def validate_df(self, df: pd.DataFrame) -> bool:
        """Return False if DataFrame is insufficient for this strategy."""
        return len(df) >= self.required_lookback
