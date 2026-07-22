"""
Data validation layer.
Checks OHLCV DataFrames before they enter the database.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from indian_swing.config.settings import settings
from indian_swing.core.exceptions import DataValidationError
from indian_swing.core.logging_setup import get_logger

logger = get_logger(__name__)

_REQUIRED_COLUMNS = {"open", "high", "low", "close", "volume"}


class OHLCVValidator:
    def __init__(self) -> None:
        self.cfg = settings.pipeline

    def validate(self, df: pd.DataFrame, symbol: str, enforce_min: bool = True) -> pd.DataFrame:
        """
        Run all validation checks. Raises DataValidationError on hard failures.
        Returns cleaned DataFrame with soft-fixed rows removed.
        """
        if df is None or df.empty:
            raise DataValidationError(f"[{symbol}] Empty DataFrame received.")

        missing = _REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise DataValidationError(f"[{symbol}] Missing columns: {missing}")

        if not isinstance(df.index, pd.DatetimeIndex):
            raise DataValidationError(f"[{symbol}] Index must be DatetimeIndex.")

        df = self._remove_duplicate_dates(df, symbol)
        df = self._remove_zero_price_rows(df, symbol)
        df = self._remove_ohlc_inconsistencies(df, symbol)
        df = self._remove_extreme_gaps(df, symbol)
        if enforce_min:
            df = self._enforce_min_records(df, symbol)

        return df

    def _remove_duplicate_dates(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        dupes = df.index.duplicated(keep="last")
        if dupes.any():
            logger.warning("validator.duplicate_dates", symbol=symbol, count=int(dupes.sum()))
            df = df[~dupes]
        return df

    def _remove_zero_price_rows(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        mask = (df["close"] <= 0) | (df["open"] <= 0) | (df["high"] <= 0) | (df["low"] <= 0)
        if mask.any():
            logger.warning("validator.zero_prices", symbol=symbol, count=int(mask.sum()))
            df = df[~mask]
        return df

    def _remove_ohlc_inconsistencies(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Remove rows where high < low or close is outside [low, high]."""
        bad = (df["high"] < df["low"]) | (df["close"] > df["high"] * 1.001) | (df["close"] < df["low"] * 0.999)
        if bad.any():
            logger.warning("validator.ohlc_inconsistency", symbol=symbol, count=int(bad.sum()))
            df = df[~bad]
        return df

    def _remove_extreme_gaps(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Remove rows with price changes > max_gap_pct (likely data errors)."""
        pct_change = df["close"].pct_change().abs() * 100
        extreme = pct_change > self.cfg.max_gap_pct
        if extreme.any():
            # logger.warning(
            #     "validator.extreme_gaps",
            #     symbol=symbol,
            #     count=int(extreme.sum()),
            #     threshold_pct=self.cfg.max_gap_pct,
            # )
            df = df[~extreme]
        return df

    def _enforce_min_records(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        if len(df) < self.cfg.min_trading_days:
            raise DataValidationError(
                f"[{symbol}] Only {len(df)} records; minimum required: {self.cfg.min_trading_days}"
            )
        return df
