from __future__ import annotations

from indian_swing.core.logging_setup import get_logger
from indian_swing.strategies.base import BaseStrategy

logger = get_logger(__name__)


class DynamicLookbackEngine:
    @staticmethod
    def get_required_lookback(strategy: BaseStrategy) -> int:
        requirements = strategy.data_requirements
        daily_from_weekly = requirements.weekly_bars * 5 if requirements.weekly_bars else 0
        benchmark = requirements.benchmark_bars or requirements.daily_bars
        result = max(requirements.total_daily_bars, daily_from_weekly + requirements.warmup_bars, benchmark)
        logger.info(
            "lookback.calculated",
            strategy=strategy.name,
            daily_bars=requirements.daily_bars,
            weekly_bars=requirements.weekly_bars,
            result=result,
        )
        return result
