"""
Volatility indicators: ATR, Bollinger Bands, Keltner Channels.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from indian_swing.indicators.base import BaseIndicator


class ATR(BaseIndicator):
    """Average True Range (Wilder's smoothing)."""

    name = "ATR"

    def compute(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        high = df["high"]
        low = df["low"]
        prev_close = df["close"].shift(1)

        tr = pd.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
            axis=1,
        ).max(axis=1)

        # Wilder's smoothing
        atr = tr.ewm(alpha=1 / period, adjust=False).mean()
        return atr


class BollingerBands(BaseIndicator):
    name = "BollingerBands"

    def compute(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
    ) -> pd.DataFrame:
        close = df["close"]
        middle = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        width = (upper - lower) / middle
        pct_b = (close - lower) / (upper - lower)

        return pd.DataFrame(
            {
                "upper": upper,
                "middle": middle,
                "lower": lower,
                "width": width,
                "pct_b": pct_b,
            },
            index=df.index,
        )


class KeltnerChannels(BaseIndicator):
    name = "KeltnerChannels"

    def compute(
        self,
        df: pd.DataFrame,
        period: int = 20,
        atr_period: int = 10,
        multiplier: float = 2.0,
    ) -> pd.DataFrame:
        from indian_swing.indicators.volatility import ATR

        middle = df["close"].ewm(span=period, adjust=False).mean()
        atr = ATR().compute(df, period=atr_period)
        upper = middle + multiplier * atr
        lower = middle - multiplier * atr

        return pd.DataFrame(
            {"upper": upper, "middle": middle, "lower": lower},
            index=df.index,
        )
