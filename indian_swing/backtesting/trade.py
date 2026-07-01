"""
Trade domain model for backtesting.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class TradeStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED_TARGET = "CLOSED_TARGET"
    CLOSED_STOP = "CLOSED_STOP"
    CLOSED_MANUAL = "CLOSED_MANUAL"
    CLOSED_EXPIRED = "CLOSED_EXPIRED"


@dataclass
class Trade:
    symbol: str
    strategy: str
    entry_date: date
    entry_price: float
    stop_loss: float
    target_1: float
    target_2: Optional[float]
    quantity: int
    direction: str = "LONG"  # LONG | SHORT

    exit_date: Optional[date] = None
    exit_price: Optional[float] = None
    status: TradeStatus = TradeStatus.OPEN

    commission: float = 0.0
    slippage: float = 0.0
    taxes: float = 0.0

    mfe: float = 0.0   # Maximum Favorable Excursion
    mae: float = 0.0   # Maximum Adverse Excursion

    partial_exits: list[dict] = field(default_factory=list)

    @property
    def gross_pnl(self) -> float:
        if self.exit_price is None:
            return 0.0
        if self.direction == "LONG":
            return (self.exit_price - self.entry_price) * self.quantity
        return (self.entry_price - self.exit_price) * self.quantity

    @property
    def net_pnl(self) -> float:
        return self.gross_pnl - self.commission - self.taxes

    @property
    def return_pct(self) -> float:
        if self.entry_price == 0:
            return 0.0
        return (self.net_pnl / (self.entry_price * self.quantity)) * 100

    @property
    def is_winner(self) -> bool:
        return self.net_pnl > 0

    @property
    def holding_days(self) -> int:
        if self.exit_date is None:
            return 0
        return (self.exit_date - self.entry_date).days

    @property
    def risk_reward_achieved(self) -> float:
        if self.exit_price is None:
            return 0.0
        reward = abs(self.exit_price - self.entry_price)
        risk = abs(self.entry_price - self.stop_loss)
        return round(reward / risk, 2) if risk > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "strategy": self.strategy,
            "entry_date": str(self.entry_date),
            "entry_price": self.entry_price,
            "exit_date": str(self.exit_date) if self.exit_date else None,
            "exit_price": self.exit_price,
            "stop_loss": self.stop_loss,
            "target_1": self.target_1,
            "quantity": self.quantity,
            "direction": self.direction,
            "gross_pnl": round(self.gross_pnl, 2),
            "net_pnl": round(self.net_pnl, 2),
            "return_pct": round(self.return_pct, 2),
            "holding_days": self.holding_days,
            "status": self.status.value,
            "mfe": round(self.mfe, 2),
            "mae": round(self.mae, 2),
            "commission": round(self.commission, 2),
        }
