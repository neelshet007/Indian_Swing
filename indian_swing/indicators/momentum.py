"""
Momentum indicators: RSI, Stochastic, Williams %R, CCI, ROC.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from indian_swing.indicators.base import BaseIndicator


class RSI(BaseIndicator):
    name = "RSI"

    def compute(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi


class Stochastic(BaseIndicator):
    name = "Stochastic"

    def compute(
        self,
        df: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3,
    ) -> pd.DataFrame:
        low_min = df["low"].rolling(window=k_period).min()
        high_max = df["high"].rolling(window=k_period).max()
        k = 100 * (df["close"] - low_min) / (high_max - low_min).replace(0, np.nan)
        d = k.rolling(window=d_period).mean()
        return pd.DataFrame({"k": k, "d": d}, index=df.index)


class WilliamsR(BaseIndicator):
    name = "WilliamsR"

    def compute(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        high_max = df["high"].rolling(window=period).max()
        low_min = df["low"].rolling(window=period).min()
        wr = -100 * (high_max - df["close"]) / (high_max - low_min).replace(0, np.nan)
        return wr


class CCI(BaseIndicator):
    name = "CCI"

    def compute(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        tp = (df["high"] + df["low"] + df["close"]) / 3
        mean_tp = tp.rolling(window=period).mean()
        mean_dev = tp.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - x.mean())), raw=True
        )
        cci = (tp - mean_tp) / (0.015 * mean_dev.replace(0, np.nan))
        return cci


class ROC(BaseIndicator):
    """Rate of Change."""

    name = "ROC"

    def compute(self, df: pd.DataFrame, period: int = 10) -> pd.Series:
        return df["close"].pct_change(periods=period) * 100
