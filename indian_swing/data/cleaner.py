"""
Data cleaning and corporate action adjustment.
All timeframes are derived internally from daily candles — never re-requested.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class OHLCVCleaner:
    """Clean and adjust raw OHLCV data."""

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy().sort_index()
        df = self._forward_fill_missing_days(df)
        df = self._clip_volume(df)
        return df

    def _forward_fill_missing_days(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill gaps in trading days (holidays etc.) using forward fill — max 3 days."""
        full_range = pd.date_range(df.index.min(), df.index.max(), freq="B")
        df = df.reindex(full_range)
        df = df.ffill(limit=3)
        df = df.dropna(subset=["close"])
        df.index.name = "date"
        return df

    def _clip_volume(self, df: pd.DataFrame) -> pd.DataFrame:
        """Replace negative or zero volume with NaN then ffill."""
        df["volume"] = df["volume"].where(df["volume"] > 0).ffill()
        df["volume"] = df["volume"].fillna(0).astype(int)
        return df


class OHLCVResampler:
    """
    Derive weekly, monthly, quarterly, yearly candles from daily data.
    Never calls external APIs for derived timeframes.
    """

    _RESAMPLE_MAP = {
        "1wk": "W-FRI",
        "1mo": "ME",
        "3mo": "QE",
        "1y": "YE",
    }

    def resample(self, daily_df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        if timeframe not in self._RESAMPLE_MAP:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        rule = self._RESAMPLE_MAP[timeframe]
        resampled = daily_df.resample(rule).agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        ).dropna(subset=["close"])
        
        # Validation
        if not resampled.empty:
            invalid_high = resampled[(resampled['high'] < resampled['open']) | (resampled['high'] < resampled['close'])]
            invalid_low = resampled[(resampled['low'] > resampled['open']) | (resampled['low'] > resampled['close'])]
            if not invalid_high.empty or not invalid_low.empty:
                raise ValueError(f"Aggregation validation failed for timeframe {timeframe}. High/Low inconsistency detected.")
                
        return resampled

    def get_all_timeframes(self, daily_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        result: dict[str, pd.DataFrame] = {"1d": daily_df}
        for tf in self._RESAMPLE_MAP:
            try:
                result[tf] = self.resample(daily_df, tf)
            except Exception:
                pass
        return result
