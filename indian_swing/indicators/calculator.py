from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from indian_swing.core.exceptions import InsufficientDataError
from indian_swing.data.cleaner import OHLCVResampler


@dataclass(frozen=True)
class IndicatorBundle:
    daily: pd.DataFrame
    weekly: pd.DataFrame
    benchmark_daily: pd.DataFrame | None = None


class IndicatorCalculator:
    _resampler = OHLCVResampler()

    @classmethod
    def build(cls, daily_df: pd.DataFrame, benchmark_df: pd.DataFrame | None = None) -> IndicatorBundle:
        daily = cls.add_daily_indicators(daily_df)
        weekly = cls.add_weekly_indicators(cls._resampler.resample(daily_df, "1wk"))
        benchmark = cls.add_daily_indicators(benchmark_df) if benchmark_df is not None and not benchmark_df.empty else None
        if benchmark is not None:
            daily = cls.add_relative_strength(daily, benchmark)
        return IndicatorBundle(daily=daily, weekly=weekly, benchmark_daily=benchmark)

    @staticmethod
    def _require_length(df: pd.DataFrame, minimum: int, scope: str) -> None:
        if df is None or df.empty or len(df) < minimum:
            raise InsufficientDataError(f"{scope} requires at least {minimum} bars, received {0 if df is None else len(df)}")

    @classmethod
    def add_daily_indicators(cls, df: pd.DataFrame) -> pd.DataFrame:
        cls._require_length(df, 252, "daily indicators")
        frame = df.copy().sort_index()

        frame["sma_20"] = frame["close"].rolling(20, min_periods=20).mean()
        frame["sma_50"] = frame["close"].rolling(50, min_periods=50).mean()
        frame["sma_150"] = frame["close"].rolling(150, min_periods=150).mean()
        frame["sma_200"] = frame["close"].rolling(200, min_periods=200).mean()
        frame["ema_20"] = frame["close"].ewm(span=20, adjust=False, min_periods=20).mean()
        frame["vol_20"] = frame["volume"].rolling(20, min_periods=20).mean()
        frame["vol_50"] = frame["volume"].rolling(50, min_periods=50).mean()
        frame["turnover_50"] = frame["vol_50"] * frame["close"]

        high_low = frame["high"] - frame["low"]
        high_close = (frame["high"] - frame["close"].shift(1)).abs()
        low_close = (frame["low"] - frame["close"].shift(1)).abs()
        frame["true_range"] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        frame["atr_14"] = frame["true_range"].rolling(14, min_periods=14).mean()

        frame["high_20"] = frame["high"].rolling(20, min_periods=20).max()
        frame["high_50"] = frame["high"].rolling(50, min_periods=50).max()
        frame["high_252"] = frame["high"].rolling(252, min_periods=252).max()
        frame["low_20"] = frame["low"].rolling(20, min_periods=20).min()
        frame["low_50"] = frame["low"].rolling(50, min_periods=50).min()
        frame["low_252"] = frame["low"].rolling(252, min_periods=252).min()
        frame["range_pct"] = ((frame["high"] - frame["low"]) / frame["close"]).replace([np.inf, -np.inf], np.nan)
        frame["price_vs_52w_high_pct"] = (frame["close"] / frame["high_252"]) - 1.0
        frame["price_vs_52w_low_pct"] = (frame["close"] / frame["low_252"]) - 1.0
        frame["sma_200_slope_20"] = frame["sma_200"] - frame["sma_200"].shift(20)
        return frame

    @classmethod
    def add_weekly_indicators(cls, weekly_df: pd.DataFrame) -> pd.DataFrame:
        cls._require_length(weekly_df, 40, "weekly indicators")
        frame = weekly_df.copy().sort_index()
        frame["sma_10w"] = frame["close"].rolling(10, min_periods=10).mean()
        frame["sma_30w"] = frame["close"].rolling(30, min_periods=30).mean()
        frame["sma_40w"] = frame["close"].rolling(40, min_periods=40).mean()
        frame["high_13w"] = frame["high"].rolling(13, min_periods=13).max()
        frame["low_13w"] = frame["low"].rolling(13, min_periods=13).min()
        frame["stage2"] = (frame["close"] > frame["sma_30w"]) & (frame["sma_30w"] > frame["sma_40w"])
        frame["weekly_uptrend"] = frame["sma_30w"] > frame["sma_30w"].shift(4)
        return frame

    @staticmethod
    def add_relative_strength(stock_daily: pd.DataFrame, benchmark_daily: pd.DataFrame) -> pd.DataFrame:
        stock = stock_daily.copy()
        benchmark = benchmark_daily[["close"]].rename(columns={"close": "benchmark_close"})
        merged = stock.join(benchmark, how="left")
        merged["benchmark_close"] = merged["benchmark_close"].ffill()
        merged["stock_return_63"] = merged["close"] / merged["close"].shift(63)
        merged["benchmark_return_63"] = merged["benchmark_close"] / merged["benchmark_close"].shift(63)
        merged["rs_ratio_63"] = merged["stock_return_63"] / merged["benchmark_return_63"]
        merged["rs_score"] = merged["rs_ratio_63"].rolling(20, min_periods=5).mean()
        return merged

    @staticmethod
    def validate_required_columns(frame: pd.DataFrame, columns: list[str]) -> None:
        missing = [column for column in columns if column not in frame.columns]
        if missing:
            raise InsufficientDataError(f"Missing indicator columns: {missing}")
        latest = frame.iloc[-1]
        invalid = [column for column in columns if pd.isna(latest[column])]
        if invalid:
            raise InsufficientDataError(f"Latest indicator values not warmed up: {invalid}")
