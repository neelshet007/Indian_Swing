"""
Volume indicators: OBV, VWAP, Volume SMA, Money Flow Index.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from indian_swing.indicators.base import BaseIndicator


class OBV(BaseIndicator):
    """On-Balance Volume."""

    name = "OBV"

    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        direction = np.sign(df["close"].diff())
        direction.iloc[0] = 0
        return (direction * df["volume"]).cumsum()


class VWAP(BaseIndicator):
    """
    Volume Weighted Average Price.
    Resets daily — works correctly on daily bars as session VWAP approximation.
    For intraday use, pass intraday OHLCV.
    """

    name = "VWAP"

    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        tp = (df["high"] + df["low"] + df["close"]) / 3
        cumulative_tpv = (tp * df["volume"]).cumsum()
        cumulative_vol = df["volume"].cumsum()
        return cumulative_tpv / cumulative_vol.replace(0, np.nan)


class VolumeSMA(BaseIndicator):
    """Simple moving average of volume — identifies above/below average volume days."""

    name = "VolumeSMA"

    def compute(self, df: pd.DataFrame, period: int = 20, **kwargs) -> pd.Series:
        return df["volume"].rolling(window=period).mean()


class MFI(BaseIndicator):
    """Money Flow Index — volume-weighted RSI."""

    name = "MFI"

    def compute(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        tp = (df["high"] + df["low"] + df["close"]) / 3
        mf = tp * df["volume"]
        pos_mf = mf.where(tp > tp.shift(1), 0)
        neg_mf = mf.where(tp < tp.shift(1), 0)
        pos_mf_sum = pos_mf.rolling(window=period).sum()
        neg_mf_sum = neg_mf.rolling(window=period).sum()
        mfr = pos_mf_sum / neg_mf_sum.replace(0, np.nan)
        return 100 - (100 / (1 + mfr))
