from __future__ import annotations

import math
from dataclasses import dataclass

from indian_swing.core.logging_setup import get_logger
from indian_swing.database.models import Stock
from indian_swing.strategies.base import StrategyContext, StrategySignal

logger = get_logger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    reason: str | None = None


class RecommendationValidator:
    def validate(
        self,
        *,
        stock: Stock,
        context: StrategyContext,
        signal: StrategySignal,
        existing_signal_keys: set[tuple[str, str, str]],
        latest_daily_date: str,
    ) -> ValidationResult:
        if not stock.id or not stock.symbol or not stock.exchange:
            return ValidationResult(False, "Invalid stock identity")
        if signal.direction.value != "LONG":
            return ValidationResult(False, "Only LONG recommendations are supported")
        if context.daily.empty or context.weekly.empty:
            return ValidationResult(False, "Missing historical context")
        if math.isnan(signal.entry_price) or math.isnan(signal.stop_loss) or math.isnan(signal.target_1):
            return ValidationResult(False, "NaN price in signal")
        if signal.stop_loss >= signal.entry_price:
            return ValidationResult(False, "Stop loss must be below entry")
        if signal.target_1 <= signal.entry_price:
            return ValidationResult(False, "Target must be above entry")
        if latest_daily_date != str(context.daily.index[-1].date()):
            return ValidationResult(False, "Stale data")
        signal_key = (stock.id, signal.metadata.get("strategy_name", ""), latest_daily_date)
        if signal_key in existing_signal_keys:
            return ValidationResult(False, "Duplicate recommendation")
        required_steps = {"Liquidity", "Trend Template", "Stage Analysis", "Weekly Trend", "Relative Strength", "VCP", "Breakout", "Risk"}
        explanation = signal.explanation or {}
        if set(explanation.keys()) != required_steps:
            return ValidationResult(False, "Incomplete explanation")
        if any(step["status"] != "PASS" for step in explanation.values()):
            return ValidationResult(False, "Strategy explanation contains failed checks")
        return ValidationResult(True)
