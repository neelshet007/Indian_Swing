"""
Shared type aliases and domain primitives.
Keep this file import-free from internal modules to avoid circular imports.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, TypeAlias

import pandas as pd


# ── Primitive aliases ─────────────────────────────────────────────────────────

Symbol: TypeAlias = str          # NSE ticker e.g. "RELIANCE.NS"
StrategyName: TypeAlias = str    # e.g. "EMABreakout"
Timeframe: TypeAlias = str       # "1d" | "1wk" | "1mo" | "3mo" | "1y"
Price: TypeAlias = float
Quantity: TypeAlias = int
Percentage: TypeAlias = float    # 0.0 – 100.0
Score: TypeAlias = float         # 0.0 – 1.0


# ── DataFrame column contracts ────────────────────────────────────────────────

OHLCV_COLUMNS: list[str] = ["open", "high", "low", "close", "volume"]
OHLCV_DTYPE: dict[str, str] = {
    "open": "float64",
    "high": "float64",
    "low": "float64",
    "close": "float64",
    "volume": "int64",
}

OHLCVFrame: TypeAlias = pd.DataFrame   # DatetimeIndex, columns = OHLCV_COLUMNS


# ── Signal direction ──────────────────────────────────────────────────────────

from enum import Enum  # noqa: E402


class SignalDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


class TimeframeEnum(str, Enum):
    DAILY = "1d"
    WEEKLY = "1wk"
    MONTHLY = "1mo"
    QUARTERLY = "3mo"
    YEARLY = "1y"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class SignalQuality(str, Enum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"


# ── Common result containers ──────────────────────────────────────────────────

from dataclasses import dataclass, field  # noqa: E402


@dataclass(frozen=True)
class PriceLevel:
    price: Price
    label: str = ""


@dataclass
class TradeSetup:
    symbol: Symbol
    entry: Price
    stop_loss: Price
    target_1: Price
    target_2: Price | None = None
    risk_reward: float = 0.0
    holding_days: int = 0

    def __post_init__(self) -> None:
        risk = abs(self.entry - self.stop_loss)
        reward = abs(self.target_1 - self.entry)
        if risk > 0:
            self.risk_reward = round(reward / risk, 2)


@dataclass
class Metadata:
    """Arbitrary key-value bag attached to signals and recommendations."""
    data: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
