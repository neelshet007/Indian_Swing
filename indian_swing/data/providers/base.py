"""
Abstract data provider interface.
All providers must implement this contract — the rest of the system never imports a concrete provider.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class DataProvider(ABC):
    """
    Provider-agnostic interface for fetching OHLCV data and stock metadata.
    Implementors handle all provider-specific pagination, auth, and rate limiting.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider identifier e.g. 'yfinance'."""
        ...

    @abstractmethod
    async def fetch_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a single symbol.

        Returns:
            DataFrame with DatetimeIndex and columns [open, high, low, close, volume].
            Empty DataFrame if no data available.
        """
        ...

    @abstractmethod
    async def fetch_bulk_ohlcv(
        self,
        symbols: list[str],
        start: date | dict[str, date],
        end: date,
        timeframe: str = "1d",
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch OHLCV for multiple symbols efficiently (batch/parallel where supported).

        Returns:
            Mapping of symbol -> DataFrame.
        """
        ...

    @abstractmethod
    async def fetch_metadata(self, symbol: str) -> dict:
        """
        Fetch company metadata: name, sector, industry, market cap, ISIN.
        Returns empty dict if unavailable.
        """
        ...

    async def health_check(self) -> bool:
        """Return True if provider is reachable. Default implementation always True."""
        return True
