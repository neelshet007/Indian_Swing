from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import pandas as pd

from indian_swing.core.types import RiskLevel, Score, SignalDirection, SignalQuality, Symbol


@dataclass(frozen=True)
class IndicatorRequirement:
    column: str
    lookback_bars: int
    timeframe: str = "1d"
    warmup_bars: int = 0


@dataclass(frozen=True)
class StrategyDataRequirements:
    daily_bars: int
    weekly_bars: int = 0
    benchmark_bars: int = 0
    benchmark_symbol: str | None = None
    warmup_bars: int = 0

    @property
    def total_daily_bars(self) -> int:
        return self.daily_bars + self.warmup_bars


@dataclass
class StrategyContext:
    symbol: str
    daily: pd.DataFrame
    weekly: pd.DataFrame
    benchmark_daily: pd.DataFrame | None = None
    as_of_date: date | None = None
    exchange: str = "NSE"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategySignal:
    symbol: Symbol
    direction: SignalDirection
    entry_price: float
    stop_loss: float
    target_1: float
    target_2: float | None
    confidence_score: Score
    quality: SignalQuality
    risk_level: RiskLevel
    holding_days: int
    reasons: list[str] = field(default_factory=list)
    explanation: dict[str, Any] = field(default_factory=dict)
    indicator_snapshot: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.entry_price = float(self.entry_price)
        self.stop_loss = float(self.stop_loss)
        self.target_1 = float(self.target_1)
        if self.target_2 is not None:
            self.target_2 = float(self.target_2)
        self.confidence_score = float(self.confidence_score)
        self.holding_days = int(self.holding_days)

    @property
    def risk_reward(self) -> float:
        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.target_1 - self.entry_price)
        return round(reward / risk, 2) if risk > 0 else 0.0

    @property
    def risk_pct(self) -> float:
        return round(abs(self.entry_price - self.stop_loss) / self.entry_price * 100, 2)


class BaseStrategy(ABC):
    _last_audit_explanation: dict[str, Any] = {}

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def indicator_requirements(self) -> tuple[IndicatorRequirement, ...]:
        return ()

    @property
    def data_requirements(self) -> StrategyDataRequirements:
        max_daily = max(
            [req.lookback_bars + req.warmup_bars for req in self.indicator_requirements if req.timeframe == "1d"],
            default=0,
        )
        max_weekly = max(
            [req.lookback_bars + req.warmup_bars for req in self.indicator_requirements if req.timeframe == "1wk"],
            default=0,
        )
        return StrategyDataRequirements(
            daily_bars=max(max_daily, 252),
            weekly_bars=max_weekly,
            warmup_bars=30,
        )

    def validate_context(self, context: StrategyContext) -> bool:
        requirements = self.data_requirements
        return len(context.daily) >= requirements.daily_bars and len(context.weekly) >= requirements.weekly_bars

    @abstractmethod
    def generate_signals(self, symbol: Symbol, context: StrategyContext) -> list[StrategySignal]:
        ...
