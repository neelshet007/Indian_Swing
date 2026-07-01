"""
Trend indicators: EMA, SMA, MACD, Supertrend, ADX.
All vectorized — no Python loops on price series.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from indian_swing.indicators.base import BaseIndicator


class EMA(BaseIndicator):
    name = "EMA"

    def compute(self, df: pd.DataFrame, period: int = 20, column: str = "close") -> pd.Series:
        return df[column].ewm(span=period, adjust=False).mean()


class SMA(BaseIndicator):
    name = "SMA"

    def compute(self, df: pd.DataFrame, period: int = 20, column: str = "close") -> pd.Series:
        return df[column].rolling(window=period).mean()


class MACD(BaseIndicator):
    name = "MACD"

    def compute(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> pd.DataFrame:
        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return pd.DataFrame(
            {"macd": macd_line, "signal": signal_line, "histogram": histogram},
            index=df.index,
        )


class ADX(BaseIndicator):
    """Average Directional Index + DI+/DI- (Wilder's)."""

    name = "ADX"

    def compute(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr = pd.concat(
            [
                high - low,
                (high - close.shift(1)).abs(),
                (low - close.shift(1)).abs(),
            ],
            axis=1,
        ).max(axis=1)

        dm_plus = (high - high.shift(1)).clip(lower=0)
        dm_minus = (low.shift(1) - low).clip(lower=0)
        dm_plus = dm_plus.where(dm_plus > dm_minus, 0)
        dm_minus = dm_minus.where(dm_minus > dm_plus, 0)

        def _wilder_smooth(series: pd.Series, n: int) -> pd.Series:
            result = series.copy() * np.nan
            result.iloc[n - 1] = series.iloc[:n].sum()
            for i in range(n, len(series)):
                result.iloc[i] = result.iloc[i - 1] - result.iloc[i - 1] / n + series.iloc[i]
            return result

        atr = _wilder_smooth(tr, period)
        di_plus = 100 * _wilder_smooth(dm_plus, period) / atr
        di_minus = 100 * _wilder_smooth(dm_minus, period) / atr
        dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus).replace(0, np.nan)
        adx = _wilder_smooth(dx.fillna(0), period)

        return pd.DataFrame(
            {"adx": adx, "di_plus": di_plus, "di_minus": di_minus},
            index=df.index,
        )


class Supertrend(BaseIndicator):
    name = "Supertrend"

    def compute(
        self,
        df: pd.DataFrame,
        period: int = 10,
        multiplier: float = 3.0,
    ) -> pd.DataFrame:
        atr = ATR().compute(df, period=period)
        hl2 = (df["high"] + df["low"]) / 2
        upper_band = hl2 + multiplier * atr
        lower_band = hl2 - multiplier * atr

        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)

        for i in range(1, len(df)):
            prev_close = df["close"].iloc[i - 1]
            curr_close = df["close"].iloc[i]

            # Adjust bands
            if lower_band.iloc[i] > lower_band.iloc[i - 1] or prev_close < lower_band.iloc[i - 1]:
                final_lower = lower_band.iloc[i]
            else:
                final_lower = lower_band.iloc[i - 1]

            if upper_band.iloc[i] < upper_band.iloc[i - 1] or prev_close > upper_band.iloc[i - 1]:
                final_upper = upper_band.iloc[i]
            else:
                final_upper = upper_band.iloc[i - 1]

            prev_st = supertrend.iloc[i - 1] if i > 1 else final_upper
            if pd.isna(prev_st) or prev_st == final_upper:
                if curr_close <= final_upper:
                    supertrend.iloc[i] = final_upper
                    direction.iloc[i] = -1  # bearish
                else:
                    supertrend.iloc[i] = final_lower
                    direction.iloc[i] = 1   # bullish
            else:
                if curr_close >= final_lower:
                    supertrend.iloc[i] = final_lower
                    direction.iloc[i] = 1
                else:
                    supertrend.iloc[i] = final_upper
                    direction.iloc[i] = -1

        return pd.DataFrame({"supertrend": supertrend, "direction": direction}, index=df.index)


# Import ATR here to avoid circular import within this module
from indian_swing.indicators.volatility import ATR  # noqa: E402
