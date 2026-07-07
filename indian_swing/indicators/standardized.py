from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def wilders_rma(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def average_true_range(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return wilders_rma(true_range, period)


def relative_strength_index(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    average_gain = wilders_rma(gain, period)
    average_loss = wilders_rma(loss, period)
    rs = average_gain / average_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))
